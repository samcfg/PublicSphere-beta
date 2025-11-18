// Form validation functions
// Returns { valid: boolean, error: string | null }

export function validateUsername(username) {
  if (!username || username.trim().length === 0) {
    return { valid: false, error: 'Username is required' };
  }
  // Add more rules as needed (alphanumeric, length limits, etc.)
  return { valid: true, error: null };
}

export function validateEmail(email) {
  // Email is optional in signup, so empty is valid
  if (!email || email.trim().length === 0) {
    return { valid: true, error: null };
  }

  // Basic email format check
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { valid: false, error: 'Invalid email format' };
  }

  return { valid: true, error: null };
}

export function validatePassword(password) {
  if (!password || password.trim().length === 0) {
    return { valid: false, error: 'Password is required' };
  }

  if (password.length < 8) {
    return { valid: false, error: 'Password must be at least 8 characters' };
  }

  return { valid: true, error: null };
}

export function validatePasswordMatch(password, passwordConfirm) {
  if (password !== passwordConfirm) {
    return { valid: false, error: 'Passwords do not match' };
  }
  return { valid: true, error: null };
}

export function validateURL(url) {
  if (!url || url.trim().length === 0) {
    return { valid: false, error: 'URL is required' };
  }

  try {
    new URL(url);
    return { valid: true, error: null };
  } catch (e) {
    return { valid: false, error: 'Invalid URL format' };
  }
}

export function validateContentLength(text, minLength = 1, maxLength = 10000) {
  if (!text || text.trim().length === 0) {
    return { valid: false, error: 'Content is required' };
  }

  if (text.length < minLength) {
    return { valid: false, error: `Content must be at least ${minLength} characters` };
  }

  if (text.length > maxLength) {
    return { valid: false, error: `Content must be less than ${maxLength} characters` };
  }

  return { valid: true, error: null };
}
