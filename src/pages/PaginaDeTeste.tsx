import React, { useState } from "react";
import { supabase } from "../lib/supabaseClient";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const PaginaDeTeste: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();
  const [resultadoDaVerificacao, setResultadoDaVerificacao] = useState<any>(null);

  React.useEffect(() => {
    const fetchVerificacao = async () => {
      if (!user?.id) return;
      setLoading(true);
      const { data, error } = await supabase
        .from("verificacao_acesso")
        .select("pode_entrar")
        .eq("id", user.id)
        .single();
      setResultadoDaVerificacao(data);
      setLoading(false);
    };
    fetchVerificacao();
  }, [user]);

  const handleVerificarAcesso = () => {
    // Checagem de segurança: resultadoDaVerificacao is set
    if (!resultadoDaVerificacao) {
      navigate("/PaginaBloqueada");
      return;
    }
    // Condição principal: pode_entrar === true
    if (resultadoDaVerificacao.pode_entrar === true) {
      window.alert("Acesso Permitido\nParabéns! Seu acesso foi verificado com sucesso.");
      // Opcional: navega para Dashboard
      // navigate("/");
    } else {
      navigate("/PaginaBloqueada");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <button
        className="px-8 py-4 rounded-lg bg-primary text-white text-xl font-semibold shadow-lg hover:bg-primary/90 transition-all"
        onClick={handleVerificarAcesso}
        disabled={loading}
      >
        Verificar Meu Acesso
      </button>
    </div>
  );
};

export default PaginaDeTeste;