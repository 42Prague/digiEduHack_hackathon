import { PieChart, Pie, Tooltip, ResponsiveContainer } from "recharts";

export function SimplePieChart({ data }: { data: { name: string; value: number }[] }) {
  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <PieChart>
          <Tooltip />
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={0}
            outerRadius={100}
            fill="#8884d8"
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
