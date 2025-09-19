# File: backend/apps/comments/admin.py
from django.contrib import admin
from .models import Comment, CommentVote

class CommentVoteInline(admin.TabularInline):
    """Inline admin for comment votes"""
    model = CommentVote
    extra = 0
    raw_id_fields = ('user',)
    readonly_fields = ('created_at',)
    max_num = 10
    verbose_name = "Vote"
    verbose_name_plural = "Votes"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment model"""
    list_display = ('id', 'author', 'thread', 'created_at', 'is_reply', 
                   'is_edited', 'is_deleted', 'vote_score')
    list_filter = ('is_edited', 'is_deleted', 'created_at')
    search_fields = ('content', 'author__username')
    readonly_fields = ('created_at', 'updated_at', 'is_reply', 'vote_score')
    raw_id_fields = ('thread', 'author', 'parent')
    
    fieldsets = (
        (None, {
            'fields': ('thread', 'author', 'content')
        }),
        ('Structure', {
            'fields': ('parent', 'is_reply')
        }),
        ('Status', {
            'fields': ('is_edited', 'is_deleted')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
        ('Votes', {
            'fields': ('vote_score',)
        }),
    )
    
    inlines = [CommentVoteInline]
    
    def is_reply(self, obj):
        """Check if comment is a reply"""
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = "Is Reply"
    
    def vote_score(self, obj):
        """Get the vote score"""
        return obj.vote_score
    vote_score.short_description = "Vote Score"
    
    actions = ['soft_delete_comments', 'restore_comments']
    
    def soft_delete_comments(self, request, queryset):
        """Soft delete selected comments"""
        queryset.update(is_deleted=True)
    soft_delete_comments.short_description = "Soft delete selected comments"
    
    def restore_comments(self, request, queryset):
        """Restore soft-deleted comments"""
        queryset.update(is_deleted=False)
    restore_comments.short_description = "Restore selected comments"


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    """Admin interface for CommentVote model"""
    list_display = ('id', 'comment', 'user', 'is_upvote', 'created_at')
    list_filter = ('is_upvote', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('comment', 'user')