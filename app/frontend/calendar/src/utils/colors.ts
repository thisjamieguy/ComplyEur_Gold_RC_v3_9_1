// Stable color per job_ref
export function colorForJob(jobRef?: string) {
  if (!jobRef) return "#16a34a";
  let h = 0;
  for (let i = 0; i < jobRef.length; i += 1) {
    h = (h * 31 + jobRef.charCodeAt(i)) >>> 0;
  }
  const hue = h % 360;
  return `hsl(${hue} 70% 50%)`;
}

