
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface PerformanceData {
  date: string;
  value: number;
}

interface PerformanceChartProps {
  data: PerformanceData[];
  isPositive: boolean;
  title: string;
  yAxisLabel?: string;
}

const PerformanceChart = ({ data, isPositive, title, yAxisLabel }: PerformanceChartProps) => {
  return (
    <div className="p-4 rounded-lg bg-card border border-border/50">
      <h3 className="text-base font-medium mb-4">{title}</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{
              top: 5,
              right: 10,
              left: 10,
              bottom: 5,
            }}
          >
            <defs>
              <linearGradient id="colorPositive" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#4CAF50" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#4CAF50" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorNegative" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#F44336" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#F44336" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 10, fill: '#999' }}
              tickLine={{ stroke: '#555' }}
            />
            <YAxis 
              tick={{ fontSize: 10, fill: '#999' }}
              tickLine={{ stroke: '#555' }}
              label={{ 
                value: yAxisLabel, 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#999', fontSize: 12 }  
              }}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1E1E1E', borderColor: '#333' }}
              labelStyle={{ color: '#fff' }}
            />
            <Area 
              type="monotone" 
              dataKey="value" 
              stroke={isPositive ? "#4CAF50" : "#F44336"} 
              fillOpacity={1} 
              fill={isPositive ? "url(#colorPositive)" : "url(#colorNegative)"} 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PerformanceChart;
