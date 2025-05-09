
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

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

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const value = payload[0].value;
    let accuracyLevel;
    let accuracyColor;
    
    if (value >= 60) {
      accuracyLevel = 'Alta';
      accuracyColor = 'text-success';
    } else if (value >= 45) {
      accuracyLevel = 'Moderada';
      accuracyColor = 'text-warning';
    } else {
      accuracyLevel = 'Baixa';
      accuracyColor = 'text-danger';
    }
    
    return (
      <div className="bg-background border border-border p-2 rounded-md shadow-md">
        <p className="text-sm font-medium">{label}</p>
        <p className={`text-sm ${accuracyColor}`}>
          Precisão: <span className="font-bold">{value}%</span>
        </p>
        <p className="text-xs text-muted-foreground">
          Assertividade {accuracyLevel}
        </p>
      </div>
    );
  }

  return null;
};

const PerformanceChart = ({ data, isPositive, title, yAxisLabel }: PerformanceChartProps) => {
  // Calculate min and max for better visualization
  const values = data.map(item => item.value);
  const minValue = Math.max(0, Math.floor(Math.min(...values) - 5));
  const maxValue = Math.min(100, Math.ceil(Math.max(...values) + 5));
  
  // Find average value
  const avgValue = values.reduce((sum, val) => sum + val, 0) / values.length;
  
  return (
    <div className="rounded-lg bg-card">
      {title && <h3 className="text-base font-medium mb-2 px-2">{title}</h3>}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{
              top: 10,
              right: 20,
              left: 10,
              bottom: 10,
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
              <linearGradient id="colorNeutral" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#FFA726" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#FFA726" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 10, fill: '#999' }}
              tickLine={{ stroke: '#555' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.2)' }}
            />
            <YAxis 
              tick={{ fontSize: 10, fill: '#999' }}
              tickLine={{ stroke: '#555' }}
              domain={[minValue, maxValue]}
              axisLine={{ stroke: 'rgba(255,255,255,0.2)' }}
              label={{ 
                value: yAxisLabel, 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#999', fontSize: 12 }  
              }}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine 
              y={50} 
              stroke="rgba(255,255,255,0.3)" 
              strokeDasharray="3 3" 
              label={{ 
                value: "50%", 
                position: "right",
                fill: "rgba(255,255,255,0.5)",
                fontSize: 10
              }} 
            />
            <ReferenceLine 
              y={avgValue} 
              stroke={isPositive ? "rgba(76,175,80,0.6)" : "rgba(244,67,54,0.6)"} 
              strokeDasharray="3 3"
              label={{ 
                value: `Média: ${avgValue.toFixed(1)}%`, 
                position: "left",
                fill: isPositive ? "rgba(76,175,80,0.8)" : "rgba(244,67,54,0.8)",
                fontSize: 10
              }}
            />
            <Area 
              type="monotone" 
              dataKey="value" 
              stroke={isPositive ? "#4CAF50" : avgValue >= 50 ? "#FFA726" : "#F44336"} 
              fillOpacity={0.8}
              fill={isPositive ? "url(#colorPositive)" : avgValue >= 50 ? "url(#colorNeutral)" : "url(#colorNegative)"} 
              activeDot={{ r: 6, stroke: "#fff", strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PerformanceChart;
