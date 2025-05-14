import React, { useEffect, useState } from 'react';
import { supabase } from '../lib/supabaseClient';

const SupabaseExample = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Reemplaza 'tu_tabla' con el nombre de una tabla real en tu base de datos
        const { data: fetchedData, error } = await supabase
          .from('tu_tabla')
          .select('*')
          .limit(10);
        
        if (error) {
          throw error;
        }
        
        setData(fetchedData);
        setLoading(false);
      } catch (error) {
        console.error('Error al obtener datos de Supabase:', error);
        setError(error.message);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Cargando datos...</div>;
  if (error) return <div>Error al cargar datos: {error}</div>;

  return (
    <div>
      <h2>Datos de Supabase</h2>
      {data.length === 0 ? (
        <p>No se encontraron datos</p>
      ) : (
        <ul>
          {data.map((item) => (
            <li key={item.id}>
              {/* Ajusta esto según la estructura de tus datos */}
              {JSON.stringify(item)}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SupabaseExample; 