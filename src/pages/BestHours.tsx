
import React from 'react';
import BestHoursExplanation from '@/components/BestHoursExplanation';

const BestHours = () => {
  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Melhores Horários dos Robôs</h1>
        <p className="text-muted-foreground mt-2">
          Entenda quando é mais adequado operar seus bots de trading
        </p>
      </div>
      
      <div className="mt-8">
        <BestHoursExplanation />
      </div>
    </div>
  );
};

export default BestHours;
