import { differenceInCalendarDays, parseISO } from "date-fns";

export function dayIndexInRange(isoDate: string, rangeStartISO: string) {
  return differenceInCalendarDays(parseISO(isoDate), parseISO(rangeStartISO));
}

export function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

