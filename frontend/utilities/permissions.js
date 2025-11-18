// Pure permission check functions
// Takes user object + resource object, returns boolean

export function canEditNode(node, currentUser) {
  if (!currentUser) return false;
  return node.created_by === currentUser.id || currentUser.is_staff;
}

export function canDeleteNode(node, currentUser) {
  if (!currentUser) return false;
  // Only staff can delete (soft delete)
  return currentUser.is_staff;
}

export function canEditConnection(edge, currentUser) {
  if (!currentUser) return false;
  return edge.created_by === currentUser.id || currentUser.is_staff;
}

export function canDeleteConnection(edge, currentUser) {
  if (!currentUser) return false;
  // Only staff can delete
  return currentUser.is_staff;
}

export function canEditComment(comment, currentUser) {
  if (!currentUser) return false;
  return comment.author_id === currentUser.id;
}

export function canDeleteComment(comment, currentUser) {
  if (!currentUser) return false;
  return comment.author_id === currentUser.id || currentUser.is_staff;
}

export function canModerate(currentUser) {
  if (!currentUser) return false;
  return currentUser.is_staff || currentUser.is_superuser;
}

export function canFlagContent(currentUser) {
  // Any logged-in user can flag content
  return !!currentUser;
}

export function canRateContent(currentUser) {
  // Any logged-in user can rate
  return !!currentUser;
}
