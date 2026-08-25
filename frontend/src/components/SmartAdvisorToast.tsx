"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { Sparkles, TrendingUp, AlertTriangle, PiggyBank, Target, X, Lightbulb } from "lucide-react";
import { generateSmartInsights, SmartInsight } from "@/lib/smartAdvisor";

export function SmartAdvisorToastManager() {
  const insightIndexRef = useRef<number>(0);
  const insightsCacheRef = useRef<SmartInsight[]>([]);

  const showNextInsight = async () => {
    // Atualizar lista de insights caso o cache esteja vazio
    if (insightsCacheRef.current.length === 0) {
      const list = await generateSmartInsights();
      insightsCacheRef.current = list;
    }

    const list = insightsCacheRef.current;
    if (list.length === 0) return;

    const insight = list[insightIndexRef.current % list.length];
    insightIndexRef.current += 1;

    // Renderizar o Toast Inteligente com design Glassmorphic Premium
    toast.custom(
      (t) => {
        let icon = <Lightbulb className="w-5 h-5 text-amber-400" />;
        let iconBg = "bg-amber-500/10 text-amber-500 border-amber-500/20";
        let badgeText = "DICA INTELIGENTE";

        if (insight.iconType === "target") {
          icon = <Target className="w-5 h-5 text-primary" />;
          iconBg = "bg-primary/10 text-primary border-primary/20";
          badgeText = "META & OBJETIVO";
        } else if (insight.iconType === "trending_up") {
          icon = <TrendingUp className="w-5 h-5 text-emerald-400" />;
          iconBg = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
          badgeText = "PROJEÇÃO FINANCEIRA";
        } else if (insight.iconType === "alert") {
          icon = <AlertTriangle className="w-5 h-5 text-rose-400" />;
          iconBg = "bg-rose-500/10 text-rose-400 border-rose-500/20";
          badgeText = "AVISO DE ORÇAMENTO";
        } else if (insight.iconType === "piggy") {
          icon = <PiggyBank className="w-5 h-5 text-cyan-400" />;
          iconBg = "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";
          badgeText = "PATRIMÓNIO & RESERVA";
        }

        return (
          <div className="w-full max-w-md bg-slate-900/95 dark:bg-slate-950/95 text-white border border-slate-700/60 dark:border-slate-800/80 backdrop-blur-xl rounded-2xl p-4 sm:p-5 shadow-2xl shadow-black/50 relative flex gap-4 items-start animate-in fade-in slide-in-from-top-4 duration-300">
            {/* Ícone com Badge */}
            <div className={`p-3 rounded-xl border shrink-0 ${iconBg}`}>
              {icon}
            </div>

            {/* Conteúdo */}
            <div className="flex-1 pr-6">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-black tracking-wider uppercase px-2 py-0.5 rounded-md bg-white/10 text-slate-300">
                  {badgeText}
                </span>
              </div>
              <h4 className="text-sm font-bold text-white mb-1.5 flex items-center gap-1.5">
                {insight.title}
              </h4>
              <p className="text-xs sm:text-[13px] text-slate-300 leading-relaxed font-medium">
                {insight.message}
              </p>
            </div>

            {/* Botão Fechar */}
            <button
              onClick={() => toast.dismiss(t)}
              className="absolute top-3 right-3 p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
              title="Fechar dica"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      },
      {
        duration: 14000 // 14 segundos visível para leitura confortável
      }
    );
  };

  useEffect(() => {
    // 1. Mostrar primeira dica inteligente 15 segundos após carregar o dashboard
    const initialTimer = setTimeout(() => {
      showNextInsight();
    }, 15000);

    // 2. Repetir a cada 10 minutos (10 * 60 * 1000 ms)
    const TEN_MINUTES_MS = 10 * 60 * 1000;
    const intervalTimer = setInterval(() => {
      showNextInsight();
    }, TEN_MINUTES_MS);

    return () => {
      clearTimeout(initialTimer);
      clearInterval(intervalTimer);
    };
  }, []);

  return null;
}
