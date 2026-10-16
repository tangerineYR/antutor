export function isValidPassword(password) {
  const length = [...password].length;
  return length >= 8 && length <= 72 && new TextEncoder().encode(password).length <= 72;
}
