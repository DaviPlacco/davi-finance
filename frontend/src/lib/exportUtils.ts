import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { api } from "./api";
import { toast } from "sonner";

// Helper for currency
const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("pt-PT", {
    style: "currency",
    currency: "EUR",
  }).format(value);
};

// Helper for date
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString("pt-PT");
};

export const exportToCSV = async () => {
  try {
    const [transactionsRes, categoriesRes] = await Promise.all([
      api.get("/transactions"), // fetches all
      api.get("/categories")
    ]);
    const transactions = transactionsRes.data;
    const categories = categoriesRes.data;

    const categoryMap = new Map(categories.map((c: any) => [c.id, c]));

    let csvContent = "Data,Categoria,Descricao,Tipo,Valor\n";

    transactions.forEach((t: any) => {
      const category = categoryMap.get(t.category_id);
      const catName = category ? category.name : "Sem Categoria";
      const typeStr = t.type === "INCOME" ? "Receita" : "Despesa";
      const valueStr = t.amount.toString().replace(".", ",");
      
      const row = `"${formatDate(t.date)}","${catName}","${t.description || ""}","${typeStr}","${valueStr}"`;
      csvContent += row + "\n";
    });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `DaviFinance_Relatorio_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error("Erro ao exportar CSV:", error);
    toast.error("Erro ao exportar CSV. Verifica a consola.");
  }
};

export const exportToPDF = async () => {
  try {
    const [transactionsRes, categoriesRes] = await Promise.all([
      api.get("/transactions"), // fetches all
      api.get("/categories")
    ]);
    const transactions = transactionsRes.data;
    const categories = categoriesRes.data;

    const categoryMap = new Map(categories.map((c: any) => [c.id, c]));

    const doc = new jsPDF();

    // Add Logo / Title
    doc.setFontSize(22);
    doc.setTextColor(79, 70, 229); // Primary Indigo-600
    doc.text("Davi Finance", 14, 20);
    
    doc.setFontSize(12);
    doc.setTextColor(100, 116, 139); // Slate-500
    doc.text(`Relatório de Transações gerado a ${formatDate(new Date().toISOString())}`, 14, 28);

    const tableColumn = ["Data", "Categoria", "Descrição", "Tipo", "Valor"];
    const tableRows: any[] = [];

    // Colors tracking for specific rows
    const rowColors: any[] = [];

    transactions.forEach((t: any) => {
      const category = categoryMap.get(t.category_id);
      const catName = category ? category.name : "Sem Categoria";
      const catColorHex = category && category.color ? category.color : "#94a3b8"; // default slate-400
      
      const typeStr = t.type === "INCOME" ? "Receita" : "Despesa";
      const valStr = formatCurrency(t.amount);

      const rowData = [
        formatDate(t.date),
        catName,
        t.description || "-",
        typeStr,
        valStr
      ];
      
      tableRows.push(rowData);
      rowColors.push({
        catColorHex,
        isIncome: t.type === "INCOME"
      });
    });

    autoTable(doc, {
      head: [tableColumn],
      body: tableRows,
      startY: 35,
      styles: { fontSize: 10, cellPadding: 3 },
      headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255] }, // slate-800
      alternateRowStyles: { fillColor: [248, 250, 252] }, // slate-50
      didParseCell: function (data) {
        if (data.section === 'body') {
          const rowIndex = data.row.index;
          const config = rowColors[rowIndex];
          
          // Color the category name column with the category color
          if (data.column.index === 1) {
             data.cell.styles.textColor = config.catColorHex;
             data.cell.styles.fontStyle = 'bold';
          }
          
          // Color the value column green/red
          if (data.column.index === 4) {
             if (config.isIncome) {
                data.cell.styles.textColor = [22, 163, 74]; // green-600
             } else {
                data.cell.styles.textColor = [220, 38, 38]; // red-600
             }
             data.cell.styles.fontStyle = 'bold';
             data.cell.styles.halign = 'right';
          }
        }
      }
    });

    doc.save(`DaviFinance_Relatorio_${new Date().toISOString().split('T')[0]}.pdf`);

  } catch (error) {
    console.error("Erro ao exportar PDF:", error);
    toast.error("Erro ao exportar PDF. Verifica a consola.");
  }
};
