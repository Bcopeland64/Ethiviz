/**
 * Calculates the average of a numeric field from an array of objects.
 * Handles nested data for image analysis results.
 * @param data Array of data items.
 * @param field The field name to average.
 * @param isImageArray If true, assumes items might have data nested under an 'analysis' key.
 * @returns The average as a number, or null if no valid data is found.
 */
export const calculateAverageScore = (
  data: any[], 
  field: string, 
  isImageArray: boolean = false
): number | null => {
  if (!data || data.length === 0) return null;
  let sum = 0;
  let count = 0;
  for (const item of data) {
    const source = isImageArray ? (item?.analysis || item) : item; // Handle potential nesting and null items
    if (source && typeof source === 'object' && source.hasOwnProperty(field)) {
      const value = parseFloat(source[field]);
      if (!isNaN(value)) {
        sum += value;
        count++;
      }
    }
  }
  return count > 0 ? sum / count : null;
};

// Add other utility functions here later as needed.
