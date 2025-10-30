declare module "color-hash" {
  export interface ColorHashOptions {
    lightness?: number | number[];
    saturation?: number | number[];
  }

  export default class ColorHash {
    constructor(options?: ColorHashOptions);
    hex(value: string): string;
    rgb(value: string): [number, number, number];
  }
}

