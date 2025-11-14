interface ChartDetails {
    chart_type: string;
    title: string;
    data: any[];
    x: string;
    y: string;
    group_by?: string[];
  }
  
  interface Props {
    generatedText: string | null;
    chartDetails: ChartDetails | null;
  }
  
  import { SimpleBarChart } from "./SimpleBarChart";
  import { SimpleLineChart } from "./SimpleLineChart";
  import { SimpleScatterChart } from "./SimpleScatterChart";
  import { SimplePieChart } from "./SimplePieChart";
  //import { SimpleHistogramChart } from "./SimpleHistogramChart";
  
  export function ResponseResults({ generatedText, chartDetails }: Props) {
  
    const noText = !generatedText;
    const noChart = !chartDetails;
  
    if (noText && noChart) {
      return (
        <div className="p-4 text-gray-500 text-sm border-l">
          Nothing to display
        </div>
      );
    }
  
    function renderChart(details: ChartDetails) {
      const type = details.chart_type;
  
      // --- Basic format: x/y mapping ------------------------------------------
      const base = details.data.map((d) => ({
        x: d[details.x],
        y: d[details.y],
      }));
  
      // --- Pie: convert to name/value ----------------------------------------
      if (type === "pie") {
        const converted = details.data.map((d) => ({
          name: d[details.x],
          value: d[details.y],
        }));
        return <SimplePieChart data={converted} />;
      }
  
      // --- Histogram: assume y contains numeric values ------------------------
    //   if (type === "histogram") {
    //     const values = details.data.map((d) => Number(d[details.y]));
    //     return <SimpleHistogramChart data={values} />;
    //   }
  
      // --- Scatter ------------------------------------------------------------
      if (type === "scatter") {
        const converted = details.data.map((d) => ({
          x: Number(d[details.x]),
          y: Number(d[details.y]),
        }));
        return <SimpleScatterChart data={converted} />;
      }
  
      // --- Line ---------------------------------------------------------------
      if (type === "line") {
        return <SimpleLineChart data={base} />;
      }
  
      // --- Bar ---------------------------------------------------------------
      if (type === "bar") {
        return <SimpleBarChart data={base} />;
      }
  
      // --- Unknown -----------------------------------------------------------
      return (
        <div className="text-red-600 p-4">
          unsupported chart type: {type}
        </div>
      );
    }
  
    const both = generatedText && chartDetails;
  
    if (both) {
      return (
        <div className="flex flex-col h-full border-l dark:bg-slate-900">
            <div className="h-[30%] overflow-y-auto p-4 bg-gray-50 dark:bg-slate-900">
                {generatedText}
            </div>

            <div className="border-t border-gray-300" />

            <div className="flex-1 overflow-auto p-4 min-h-0 h-full">
                <div className="text-lg font-semibold mb-2">
                {chartDetails.title}
                </div>
                {renderChart(chartDetails)}
            </div>

            </div>
      );
    }
  
    if (generatedText && !chartDetails) {
      return (
        <div className="h-full overflow-y-auto p-4 border-l bg-gray-50 dark:bg-slate-900">
          {generatedText}
        </div>
      );
    }
  
    return (
      <div className="h-full overflow-auto p-4 border-l">
        <div className="text-lg font-semibold mb-2">
          {chartDetails?.title}
        </div>
        {chartDetails ? renderChart(chartDetails) : null}
      </div>
    );
  }
  