"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Save, Phone, Info } from "lucide-react";
import { toast } from "sonner";

export default function ConfiguracoesPage() {
  const [whatsappNumber, setWhatsappNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await api.get("/users/me");
      if (response.data.whatsapp_number) {
        setWhatsappNumber(response.data.whatsapp_number);
      }
    } catch (error) {
      console.error("Erro ao carregar configurações", error);
      toast.error("Erro ao carregar as tuas configurações.");
    } finally {
      setFetching(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    // Limpar o número para conter apenas dígitos e o sinal de mais
    const cleanNumber = whatsappNumber.replace(/[^\d+]/g, '');

    try {
      await api.put("/users/me/settings", {
        whatsapp_number: cleanNumber,
        whatsapp_report_frequency: "off"
      });
      toast.success("Configurações guardadas com sucesso!");
    } catch (error) {
      console.error("Erro ao guardar configurações", error);
      toast.error("Não foi possível guardar as configurações.");
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return <div className="p-8 text-center text-slate-500 dark:text-slate-400">A carregar configurações...</div>;
  }

  return (
    <div className="p-4 md:p-8 max-w-4xl mx-auto w-full">
      
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Integrações</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-2">Gere as tuas preferências e integrações da plataforma.</p>
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-6 md:p-8">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-6 flex items-center gap-2">
          <Phone className="w-5 h-5 text-green-500" />
          Integração WhatsApp
        </h2>
        
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4 mb-6 flex gap-3">
          <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-blue-800 dark:text-blue-300">
            Adiciona o teu número de WhatsApp para poderes enviar os teus relatórios financeiros diretamente para o teu telemóvel com um único clique.
          </p>
        </div>

        <form onSubmit={handleSave} className="space-y-6">
          <div>
            <label htmlFor="whatsapp" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Número de WhatsApp (com indicativo)
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-slate-500 dark:text-slate-400">+</span>
              </div>
              <input
                type="text"
                id="whatsapp"
                value={whatsappNumber}
                onChange={(e) => setWhatsappNumber(e.target.value)}
                className="w-full pl-8 pr-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary dark:text-white transition-all"
                placeholder="Ex: 351912345678"
              />
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
              Não te esqueças de incluir o código do país (ex: 351 para Portugal, 55 para o Brasil).
            </p>
          </div>

          <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 px-6 py-3 bg-primary hover:bg-primary/90 text-white font-medium rounded-xl transition-all disabled:opacity-50"
            >
              {loading ? (
                "A guardar..."
              ) : (
                <>
                  <Save className="w-4 h-4" /> Guardar Alterações
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
