import React, { useState } from 'react';
import { Clock } from 'lucide-react';
const BestHoursExplanation = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  return <div className="bg-gradient-to-r from-primary/5 to-primary/10 rounded-lg p-6 animate-fade-in">
      <div className="flex items-center gap-3 mb-3">
        <div className="bg-primary/20 p-3 rounded-full">
          <Clock className="text-primary" size={24} />
        </div>
        <h2 className="text-xl font-semibold">Mejores Horarios de los Robots</h2>
      </div>

      <div className={`overflow-hidden transition-all duration-500 ${isExpanded ? 'max-h-[1000px]' : 'max-h-28'}`}>
        <p className="text-muted-foreground mb-4">
          <strong className="text-foreground">No existe un horario "mejor" para operar los robots.</strong> El rendimiento de los bots 
          en el mercado de índices sintéticos, como el R_100, no es predecible por horario del día, ya que estos mercados están basados 
          en algoritmos de números pseudoaleatorios que no siguen patrones temporales.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
          <div className="bg-background rounded-lg p-4 shadow-sm border border-border">
            <h3 className="font-medium mb-2 text-primary">1. Prueba en Cuenta Demo</h3>
            <p className="text-sm">Siempre comienza probando el bot en la cuenta de demostración para observar si está teniendo una buena asertividad. Si es asertivo, colócalo en la cuenta real. De lo contrario, vuelve en otro horario.</p>
          </div>

          <div className="bg-background rounded-lg p-4 shadow-sm border border-border">
            <h3 className="font-medium mb-2 text-primary">2. Analiza el Escenario</h3>
            <p className="text-sm">Observa si el bot está presentando una secuencia positiva o negativa. Si el robot está con una secuencia positiva, cambia a la cuenta real; si está negativa, vuelve en otro horario.</p>
          </div>

          <div className="bg-background rounded-lg p-4 shadow-sm border border-border">
            <h3 className="font-medium mb-2 text-primary">3. Gestión de Riesgo</h3>
            <p className="text-sm">Más importante que el horario es definir límites claros de pérdidas (Stop Loss) y ganancias (Stop Win) antes de iniciar cualquier operación automatizada. Simula tu gestión de riesgos en la cuenta demo antes de iniciar en la real.</p>
          </div>
        </div>

        <div className="bg-primary/5 rounded-lg p-4 border border-primary/20">
          <h3 className="font-medium mb-2 text-primary flex items-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
            Consejo Profesional
          </h3>
          <p className="text-sm">En vez de enfocarte en horarios específicos, concéntrate en:</p>
          <ul className="text-sm mt-2 space-y-2">
            <li className="flex items-start">
              <span className="bg-primary/20 text-primary rounded-full w-5 h-5 flex items-center justify-center mr-2 mt-0.5">✓</span>
              <span>Probar el bot en diferentes momentos para entender su comportamiento en varios escenarios</span>
            </li>
            <li className="flex items-start">
              <span className="bg-primary/20 text-primary rounded-full w-5 h-5 flex items-center justify-center mr-2 mt-0.5">✓</span>
              <span>Ajustar los parámetros de gestión de riesgo basados en los resultados observados</span>
            </li>
            <li className="flex items-start">
              <span className="bg-primary/20 text-primary rounded-full w-5 h-5 flex items-center justify-center mr-2 mt-0.5">✓</span>
              <span>Siempre usar valores que puedas permitirte perder</span>
            </li>
          </ul>
        </div>
      </div>
      
      <button onClick={() => setIsExpanded(!isExpanded)} className="mt-4 text-primary hover:text-primary/80 text-sm font-medium flex items-center mx-auto">
        {isExpanded ? 'Mostrar menos' : 'Conoce más sobre horarios'}
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={`ml-1 transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
          <path d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    </div>;
};
export default BestHoursExplanation;