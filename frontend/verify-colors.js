/**
 * Color Contrast Verification Script
 * Verifies WCAG AAA compliance for Clew Directive terminal theme
 */

// Convert hex to RGB
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

// Calculate relative luminance
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

// Calculate contrast ratio
function getContrastRatio(hex1, hex2) {
  const rgb1 = hexToRgb(hex1);
  const rgb2 = hexToRgb(hex2);
  
  if (!rgb1 || !rgb2) return 0;
  
  const lum1 = getLuminance(rgb1.r, rgb1.g, rgb1.b);
  const lum2 = getLuminance(rgb2.r, rgb2.g, rgb2.b);
  
  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

// Test colors
const colors = {
  bgPrimary: '#0A1128',
  textPrimary: '#FFD60A',
  textDim: '#B8A000',
};

console.log('═══════════════════════════════════════════════════════');
console.log('  CLEW DIRECTIVE - COLOR CONTRAST VERIFICATION');
console.log('═══════════════════════════════════════════════════════\n');

console.log('Colors:');
console.log(`  Background (Osprey Navy): ${colors.bgPrimary}`);
console.log(`  Primary Text (Cyber Gold): ${colors.textPrimary}`);
console.log(`  Dim Text (Muted Gold): ${colors.textDim}\n`);

// Test primary text contrast
const primaryContrast = getContrastRatio(colors.bgPrimary, colors.textPrimary);
console.log('Primary Text Contrast:');
console.log(`  Ratio: ${primaryContrast.toFixed(2)}:1`);
console.log(`  WCAG AA (4.5:1): ${primaryContrast >= 4.5 ? '✓ PASS' : '✗ FAIL'}`);
console.log(`  WCAG AAA (7:1): ${primaryContrast >= 7 ? '✓ PASS' : '✗ FAIL'}\n`);

// Test dim text contrast
const dimContrast = getContrastRatio(colors.bgPrimary, colors.textDim);
console.log('Dim Text Contrast:');
console.log(`  Ratio: ${dimContrast.toFixed(2)}:1`);
console.log(`  WCAG AA (4.5:1): ${dimContrast >= 4.5 ? '✓ PASS' : '✗ FAIL'}`);
console.log(`  WCAG AAA (7:1): ${dimContrast >= 7 ? '✓ PASS' : '✗ FAIL'}\n`);

console.log('═══════════════════════════════════════════════════════');
console.log('  OVERALL RESULT');
console.log('═══════════════════════════════════════════════════════');

if (primaryContrast >= 7 && dimContrast >= 4.5) {
  console.log('  ✓ ALL TESTS PASSED');
  console.log('  Theme meets WCAG AAA for primary text');
  console.log('  Theme meets WCAG AA for dim text');
} else {
  console.log('  ✗ SOME TESTS FAILED');
  console.log('  Please adjust colors to meet WCAG standards');
}

console.log('═══════════════════════════════════════════════════════\n');
