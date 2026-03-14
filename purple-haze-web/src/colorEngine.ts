import Color from "colorjs.io";

export interface SwatchData {
  hex: string;
  lightness: number; // CIE L* for reference
}

export interface InterpolationRow {
  space: string;
  label: string;
  description: string;
  swatches: SwatchData[];
}

const STEPS = 13;

function colorToHex(color: Color): string {
  const srgb = color.to("srgb").toGamut({ space: "srgb" });
  return srgb.toString({ format: "hex" });
}

function getLightness(color: Color): number {
  return color.to("lab-d65").coords[0] ?? 0;
}

/**
 * Interpolate from `startHex` to `endHex` in the given color space,
 * producing `steps` evenly-spaced swatches.
 */
function interpolateInSpace(
  startHex: string,
  endHex: string,
  space: string,
  steps: number
): SwatchData[] {
  const start = new Color(startHex);
  const end = new Color(endHex);

  const range = Color.range(start, end, { space, outputSpace: space });
  const swatches: SwatchData[] = [];

  for (let i = 0; i < steps; i++) {
    const t = i / (steps - 1);
    const color = range(t);
    swatches.push({
      hex: colorToHex(color),
      lightness: Math.round(getLightness(color) * 10) / 10,
    });
  }

  return swatches;
}

/**
 * For a given input color, generate interpolation rows across
 * multiple color spaces, tweening to white and to black.
 */
export function generateRows(inputHex: string): {
  toWhite: InterpolationRow[];
  toBlack: InterpolationRow[];
} {
  const spaces = [
    {
      space: "srgb",
      label: "sRGB",
      description: "Naive linear interpolation in gamma-encoded sRGB",
    },
    {
      space: "hsl",
      label: "HSL",
      description: "Cylindrical sRGB — hue preserved, but perceptually uneven",
    },
    {
      space: "lab-d65",
      label: "CIE L*a*b*",
      description:
        "Perceptually uniform (1976) — prone to purple hue shift on blues",
    },
    {
      space: "lch",
      label: "CIE LCH",
      description: "Cylindrical Lab — hue angle preserved, but uneven chroma",
    },
    {
      space: "oklab",
      label: "OKLab",
      description:
        "Improved perceptual uniformity (Björn Ottosson, 2020) — fixes the purple shift",
    },
    {
      space: "oklch",
      label: "OKLch",
      description:
        "Cylindrical OKLab — best of both worlds: uniform + hue stable",
    },
    {
      space: "cam16-jmh",
      label: "CAM16",
      description:
        "CIE Color Appearance Model (2016) — accounts for viewing conditions",
    },
    {
      space: "hct",
      label: "HCT",
      description:
        "Google Material Design 3 — CAM16 hue/chroma + CIE L* tone",
    },
    {
      space: "jzazbz",
      label: "Jzazbz",
      description:
        "HDR-ready perceptually uniform space (Safdar 2017)",
    },
  ];

  const toWhite: InterpolationRow[] = [];
  const toBlack: InterpolationRow[] = [];

  for (const { space, label, description } of spaces) {
    toWhite.push({
      space,
      label,
      description,
      swatches: interpolateInSpace(inputHex, "#ffffff", space, STEPS),
    });
    toBlack.push({
      space,
      label,
      description,
      swatches: interpolateInSpace(inputHex, "#000000", space, STEPS),
    });
  }

  return { toWhite, toBlack };
}
