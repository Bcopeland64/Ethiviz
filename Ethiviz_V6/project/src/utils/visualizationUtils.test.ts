import { calculateAverageScore } from './visualizationUtils';

describe('calculateAverageScore', () => {
  it('should return null for an empty array', () => {
    expect(calculateAverageScore([], 'score')).toBeNull();
  });

  it('should calculate the average correctly for valid numbers', () => {
    const data = [{ score: 10 }, { score: 20 }, { score: 30 }];
    expect(calculateAverageScore(data, 'score')).toBe(20);
  });

  it('should ignore non-numeric values and missing fields', () => {
    const data = [{ score: 10 }, { score: 'abc' }, {}, { value: 20 }, { score: 20 }];
    expect(calculateAverageScore(data, 'score')).toBe(15); // (10 + 20) / 2
  });
  
  it('should return null if no valid numeric scores are found', () => {
    const data = [{ score: 'abc' }, { score: 'def' }];
    expect(calculateAverageScore(data, 'score')).toBeNull();
  });

  it('should handle isImageArray=true with data nested under analysis key', () => {
    const data = [
      { analysis: { score: 10 } }, 
      { analysis: { score: 20 } },
      { somethingelse: { score: 100} } // no analysis key, should be ignored
    ];
    expect(calculateAverageScore(data, 'score', true)).toBe(15); // (10+20)/2
  });

  it('should handle isImageArray=true with data directly on items if analysis key is missing', () => {
    const data = [{ score: 10 }, { score: 30 }]; // No 'analysis' key
    // The function logic is: const source = isImageArray ? (item?.analysis || item) : item;
    // So if item.analysis is undefined, it will use 'item' itself.
    expect(calculateAverageScore(data, 'score', true)).toBe(20);
  });
  
  it('should handle isImageArray=true with mixed direct and nested data', () => {
    const data = [
      { analysis: { score: 10 } }, 
      { score: 20 }, // direct, analysis is undefined, so 'item' is used
      { analysis: { score: 30 } },
    ];
    expect(calculateAverageScore(data, 'score', true)).toBe(20); // (10+20+30)/3
  });

  it('should handle items being null or undefined in the array', () => {
    const dataWithNull = [{ score: 10 }, null, { score: 20 }, undefined, { score: 30 }];
    expect(calculateAverageScore(dataWithNull, 'score', false)).toBe(20); // (10+20+30)/3

    const dataWithNullForImage = [
      { analysis: { score: 10 } }, 
      null, 
      { score: 20 }, // direct
      undefined, 
      { analysis: { score: 30 } }
    ];
    // (10 from first, 20 from third (direct), 30 from fifth) / 3 = 20
    expect(calculateAverageScore(dataWithNullForImage, 'score', true)).toBe(20); 
  });
  
  it('should handle field not existing in any object', () => {
    const data = [{ value: 10 }, { value: 20 }];
    expect(calculateAverageScore(data, 'score')).toBeNull();
  });

  it('should handle array of non-objects', () => {
    const data = [10, 20, 30] as any; // Force non-object array
    expect(calculateAverageScore(data, 'score')).toBeNull();
  });

  it('should handle all items having the field as non-numeric', () => {
    const data = [{score: 'ten'}, {score: 'twenty'}];
    expect(calculateAverageScore(data, 'score')).toBeNull();
  });

  it('should handle isImageArray=true where some analysis objects are null or dont have the field', () => {
    const data = [
      { analysis: { score: 10 } },
      { analysis: null }, // null analysis object
      { analysis: { value: 50 } }, // analysis object exists but no 'score' field
      { analysis: { score: 20 } },
      { item: { score: 99 } } // no 'analysis' field, but isImageArray is true
    ];
    // (10 + 20) / 2 = 15. The last item is ignored because item.analysis is undefined, so it falls back to item, but item.score is not picked up.
    // The logic `const source = isImageArray ? (item?.analysis || item) : item;` means if item.analysis is undefined, source becomes item.
    // If item is `{ item: { score: 99 } }`, then source is `{ item: { score: 99 } }`. `source.hasOwnProperty('score')` is false.
    // This is the current behavior of calculateAverageScore.
    expect(calculateAverageScore(data, 'score', true)).toBe(15);
  });

  it('should handle a mix of valid and invalid (null/undefined) items for isImageArray=true', () => {
    const data = [
      { analysis: { score: 10 } },
      null,
      { analysis: { score: 20 } },
      undefined,
      { score: 30 }, // direct score, used because item.analysis is undefined
      { analysis: { score: 'invalid' } },
      { analysis: {} } // analysis object exists, but no score field
    ];
    // (10 + 20 + 30) / 3 = 20
    expect(calculateAverageScore(data, 'score', true)).toBe(20);
  });

});
