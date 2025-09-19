# File: backend/apps/comments/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, F, Sum, Case, When, IntegerField
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import Comment, CommentVote
from .serializers import CommentSerializer, CommentDetailSerializer, CommentVoteSerializer
from utils.permissions import IsAuthorOrReadOnly, IsModeratorOrReadOnly
from apps.forums.models import Thread


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comments.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['thread', 'author', 'parent']
    search_fields = ['content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['created_at']
    
    def get_queryset(self):
        """Filter comments based on query parameters"""
        queryset = Comment.objects.all()
        
        # Filter by thread
        thread_id = self.request.query_params.get('thread_id')
        if thread_id:
            queryset = queryset.filter(thread_id=thread_id)
        
        # Filter top-level comments only if specified
        top_level_only = self.request.query_params.get('top_level_only') == 'true'
        if top_level_only:
            queryset = queryset.filter(parent__isnull=True)
        
        # Include vote count annotation
        queryset = queryset.annotate(
            vote_count=Sum(
                Case(
                    When(votes__is_upvote=True, then=1),
                    When(votes__is_upvote=False, then=-1),
                    default=0,
                    output_field=IntegerField()
                )
            )
        )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer class"""
        if self.action == 'retrieve':
            return CommentDetailSerializer
        return self.serializer_class
    
    def perform_create(self, serializer):
        """Save comment with current user as author"""
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upvote(self, request, pk=None):
        """Upvote a comment"""
        comment = self.get_object()
        
        # Get or create the vote
        vote, created = CommentVote.objects.get_or_create(
            comment=comment,
            user=request.user,
            defaults={'is_upvote': True}
        )
        
        # If vote already existed but wasn't an upvote, change it
        if not created and not vote.is_upvote:
            vote.is_upvote = True
            vote.save()
        
        # Return updated comment
        serializer = self.get_serializer(comment)
        return Response(serializer.data)
        
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def downvote(self, request, pk=None):
        """Downvote a comment"""
        comment = self.get_object()
        
        # Get or create the vote
        vote, created = CommentVote.objects.get_or_create(
            comment=comment,
            user=request.user,
            defaults={'is_upvote': False}
        )
        
        # If vote already existed but was an upvote, change it
        if not created and vote.is_upvote:
            vote.is_upvote = False
            vote.save()
        
        # Return updated comment
        serializer = self.get_serializer(comment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_vote(self, request, pk=None):
        """Remove vote from a comment"""
        comment = self.get_object()
        
        # Delete vote if it exists
        CommentVote.objects.filter(comment=comment, user=request.user).delete()
        
        # Return updated comment
        serializer = self.get_serializer(comment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def soft_delete(self, request, pk=None):
        """Soft delete a comment"""
        comment = self.get_object()
        
        # Check if user has permission
        if request.user != comment.author and not request.user.is_staff:
            return Response(
                {"detail": "You don't have permission to delete this comment."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete
        comment.is_deleted = True
        comment.save()
        
        return Response({"detail": "Comment soft deleted successfully"})
    
    @action(detail=False, methods=['get'])
    def for_thread(self, request):
        """Get comments for a specific thread"""
        thread_id = request.query_params.get('thread_id')
        if not thread_id:
            return Response(
                {"detail": "thread_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        thread = get_object_or_404(Thread, id=thread_id)
        
        # Get ALL comments for thread (including replies), not just top-level
        comments = self.get_queryset().filter(
            thread=thread
            # Removed: parent__isnull=True
        ).order_by('created_at')  # Chronological order for tree building
        
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get replies to a specific comment"""
        comment = self.get_object()
        replies = self.get_queryset().filter(parent=comment).order_by('created_at')
        
        page = self.paginate_queryset(replies)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data)


class CommentVoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for comment votes.
    """
    queryset = CommentVote.objects.all()
    serializer_class = CommentVoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['comment', 'user', 'is_upvote']
    
    def get_queryset(self):
        """Limit votes to those by current user"""
        user = self.request.user
        return CommentVote.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Save vote with current user"""
        serializer.save(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Override create to handle existing votes"""
        comment_id = request.data.get('comment')
        is_upvote = request.data.get('is_upvote', True)
        
        if not comment_id:
            return Response(
                {"detail": "comment field is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if comment exists
        comment = get_object_or_404(Comment, id=comment_id)
        
        # Try to get existing vote
        try:
            vote = CommentVote.objects.get(comment=comment, user=request.user)
            
            # Update vote if different
            if vote.is_upvote != is_upvote:
                vote.is_upvote = is_upvote
                vote.save()
                serializer = self.get_serializer(vote)
                return Response(serializer.data)
            else:
                # Return existing vote
                serializer = self.get_serializer(vote)
                return Response(serializer.data)
                
        except CommentVote.DoesNotExist:
            # Create new vote
            return super().create(request, *args, **kwargs)