/**
 * Get Bootstrap icon class for a given file type
 * @param {string} fileType - MIME type of the file
 * @returns {string} Bootstrap icon class name
 */
export const getFileIcon = (fileType) => {
  if (fileType.startsWith('image/')) return 'bi-image';
  if (fileType.includes('pdf')) return 'bi-file-pdf';
  if (fileType.includes('word') || fileType.includes('document')) return 'bi-file-word';
  if (fileType.includes('excel') || fileType.includes('spreadsheet')) return 'bi-file-earmark-spreadsheet';
  if (fileType.includes('zip') || fileType.includes('compressed')) return 'bi-file-zip';
  return 'bi-paperclip';
};

/**
 * Format file size in bytes to human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size (e.g., "1.5 MB")
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};

