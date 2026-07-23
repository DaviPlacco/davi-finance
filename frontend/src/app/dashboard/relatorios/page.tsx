"use client";

import { useState } from "react";
import { Download, FileText, Calendar, CheckCircle } from "lucide-react";
import { CustomSelect } from "@/components/CustomSelect";
import { toast } from "sonner";
import { exportGeneralMonthlyReportPDF, generateWhatsappReport } from "@/lib/exportUtils";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function RelatoriosPage() {
  const currentYear = new Date().getFullYear().toString();
  const currentMonth = (new Date().getMonth() + 1).toString();
  const router = useRouter();
  
  const [filterYear, setFilterYear] = useState(currentYear);
  const [filterMonth, setFilterMonth] = useState(currentMonth);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSending, setIsSending] = useState(false);

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    try {
      await exportGeneralMonthlyReportPDF(parseInt(filterYear), parseInt(filterMonth));
      toast.success("Relatório gerado com sucesso!");
    } catch (error) {
      toast.error("Erro ao gerar relatório.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleWhatsappSend = async () => {
    setIsSending(true);
    try {
      // 1. Check if user has WhatsApp number
      const userRes = await api.get("/users/me");
      const whatsappNumber = userRes.data.whatsapp_number;

      if (!whatsappNumber) {
        toast.error("Número de WhatsApp não configurado.");
        router.push("/dashboard/configuracoes");
        return;
      }

      // 2. Generate Report Text
      const text = await generateWhatsappReport(parseInt(filterYear), parseInt(filterMonth));
      
      // 3. Open WhatsApp Web or App
      const encodedText = encodeURIComponent(text);
      const waUrl = `https://wa.me/${whatsappNumber}?text=${encodedText}`;
      
      window.open(waUrl, "_blank");
      toast.success("A abrir o WhatsApp...");
    } catch (error) {
      console.error(error);
      toast.error("Erro ao gerar relatório para WhatsApp.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Relatórios de Fim de Mês</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">Gera um resumo completo do teu desempenho financeiro mensal.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="glass-card p-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-primary/10 rounded-xl">
              <Calendar className="w-6 h-6 text-primary" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Selecionar Período</h2>
          </div>

          <div className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Ano</label>
              <CustomSelect 
                value={filterYear} 
                onChange={setFilterYear as any} 
                options={[
                  { value: "2025", label: "2025" },
                  { value: "2026", label: "2026" }
                ]} 
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Mês</label>
              <CustomSelect 
                value={filterMonth} 
                onChange={setFilterMonth as any} 
                options={[
                  { value: "1", label: "Janeiro" },
                  { value: "2", label: "Fevereiro" },
                  { value: "3", label: "Março" },
                  { value: "4", label: "Abril" },
                  { value: "5", label: "Maio" },
                  { value: "6", label: "Junho" },
                  { value: "7", label: "Julho" },
                  { value: "8", label: "Agosto" },
                  { value: "9", label: "Setembro" },
                  { value: "10", label: "Outubro" },
                  { value: "11", label: "Novembro" },
                  { value: "12", label: "Dezembro" }
                ]} 
              />
            </div>

            <div className="flex flex-col gap-3">
              <button 
                onClick={handleGenerateReport}
                disabled={isGenerating}
                className="w-full flex items-center justify-center gap-2 py-4 bg-primary text-white font-bold rounded-xl shadow-lg shadow-primary/30 hover:bg-primary/90 transition-all disabled:opacity-70"
              >
                {isGenerating ? (
                  <>A gerar documento...</>
                ) : (
                  <>
                    <Download className="w-5 h-5" /> Exportar PDF Completo
                  </>
                )}
              </button>
              
              <button 
                onClick={handleWhatsappSend}
                disabled={isSending}
                className="w-full flex items-center justify-center gap-2 py-4 bg-[#25D366] text-white font-bold rounded-xl shadow-lg shadow-[#25D366]/30 hover:bg-[#1DA851] transition-all disabled:opacity-70"
              >
                {isSending ? (
                  <>A preparar envio...</>
                ) : (
                  <>
                    <FileText className="w-5 h-5" /> Enviar por WhatsApp
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="glass-card p-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-xl">
              <FileText className="w-6 h-6 text-slate-600 dark:text-slate-300" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">O que inclui o relatório?</h2>
          </div>
          
          <ul className="space-y-4">
            <li className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-slate-900 dark:text-white">Resumo Geral</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">Total de receitas, despesas e saldo líquido do mês.</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-slate-900 dark:text-white">Lista de Transações</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">Detalhamento completo de todos os movimentos categorizados.</p>
              </div>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-slate-900 dark:text-white">Estado dos Investimentos</p>
                <p className="text-sm text-slate-500 dark:text-slate-400">Posição atual da tua carteira de ativos (património).</p>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
