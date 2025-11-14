import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export function buildHistogram(values: number[], binCount = 10) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const size = (max - min) / binCount;

  const bins = Array.from({ length: binCount }, (_, i) => ({
    x: `${(min + i * size).toFixed(1)} – ${(min + (i + 1) * size).toFixed(1)}`,
    y: 0
  }));

  values.forEach(v => {
    const idx = Math.min(Math.floor((v - min) / size), binCount - 1);
    bins[idx].y += 1;
  });

  return bins;
}

export function SimpleHistogram({ data }: { data: number[] }) {
  const bins = buildHistogram(data, 10);

  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <BarChart data={bins}>
          <XAxis dataKey="x" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="y" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}