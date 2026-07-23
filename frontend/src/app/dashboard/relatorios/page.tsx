"use client";

import { useState, useEffect, useMemo } from "react";
import { Download, FileText, Calendar, CheckCircle, Clock } from "lucide-react";
import { CustomSelect } from "@/components/CustomSelect";
import { toast } from "sonner";
import { exportGeneralMonthlyReportPDF } from "@/lib/exportUtils";
import { api } from "@/lib/api";

type ReportHistory = {
  year: number;
  month: number;
  income: number;
  expense: number;
  balance: number;
};

export default function RelatoriosPage() {
  const currentYear = new Date().getFullYear().toString();
  const currentMonth = (new Date().getMonth() + 1).toString();
  
  const [filterYear, setFilterYear] = useState(currentYear);
  const [filterMonth, setFilterMonth] = useState(currentMonth);
  const [isGenerating, setIsGenerating] = useState(false);

  const [history, setHistory] = useState<ReportHistory[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  useEffect(() => {
    // Read global itemsPerPage setting
    const savedItemsPerPage = localStorage.getItem("itemsPerPage");
    if (savedItemsPerPage) {
      setItemsPerPage(parseInt(savedItemsPerPage, 10));
    }

    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await api.get("/reports/history");
      setHistory(response.data);
    } catch (error) {
      console.error("Erro ao carregar histórico", error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleGenerateReport = async (year?: number, month?: number) => {
    setIsGenerating(true);
    try {
      await exportGeneralMonthlyReportPDF(year || parseInt(filterYear), month || parseInt(filterMonth));
      toast.success("Relatório gerado com sucesso!");
    } catch (error) {
      toast.error("Erro ao gerar relatório.");
    } finally {
      setIsGenerating(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(value);
  };
  
  const getMonthName = (month: number) => {
    const months = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
    return months[month - 1];
  };

  const totalPages = Math.ceil(history.length / itemsPerPage) || 1;
  const currentHistory = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return history.slice(start, start + itemsPerPage);
  }, [history, currentPage, itemsPerPage]);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-6xl mx-auto pb-10">
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
                  { value: "2024", label: "2024" },
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
                options={Array.from({length: 12}, (_, i) => ({ value: (i + 1).toString(), label: getMonthName(i + 1) }))} 
              />
            </div>

            <button 
              onClick={() => handleGenerateReport()}
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

      <div className="glass-card p-8 mt-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-indigo-100 dark:bg-indigo-900/30 rounded-xl">
            <Clock className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Histórico de Relatórios</h2>
        </div>

        {loadingHistory ? (
          <div className="text-center py-8 text-slate-500">A carregar histórico...</div>
        ) : history.length === 0 ? (
          <div className="text-center py-8 text-slate-500">Ainda não tens dados suficientes para gerar histórico.</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-sm text-slate-500 dark:text-slate-400">
                    <th className="pb-3 font-semibold">Período</th>
                    <th className="pb-3 font-semibold text-right">Receitas</th>
                    <th className="pb-3 font-semibold text-right">Despesas</th>
                    <th className="pb-3 font-semibold text-right">Saldo</th>
                    <th className="pb-3 font-semibold text-center">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {currentHistory.map((item, index) => (
                    <tr key={index} className="border-b border-slate-100 dark:border-slate-800/50 hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-colors">
                      <td className="py-4">
                        <div className="font-bold text-slate-900 dark:text-white">{getMonthName(item.month)} {item.year}</div>
                      </td>
                      <td className="py-4 text-right text-green-600 font-medium">{formatCurrency(item.income)}</td>
                      <td className="py-4 text-right text-red-600 font-medium">{formatCurrency(item.expense)}</td>
                      <td className={`py-4 text-right font-bold ${item.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(item.balance)}
                      </td>
                      <td className="py-4 text-center">
                        <button
                          onClick={() => handleGenerateReport(item.year, item.month)}
                          className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-primary hover:text-white dark:hover:bg-primary transition-colors text-sm font-medium"
                        >
                          <Download className="w-4 h-4" /> PDF
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Paginação */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100 dark:border-slate-800">
                <div className="text-sm text-slate-500">
                  Página <span className="font-bold text-slate-900 dark:text-white">{currentPage}</span> de {totalPages}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 bg-slate-100 dark:bg-slate-800 rounded-md disabled:opacity-50 text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 bg-slate-100 dark:bg-slate-800 rounded-md disabled:opacity-50 text-sm font-medium hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
                  >
                    Próxima
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
