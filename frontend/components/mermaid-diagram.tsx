"use client";

import { useEffect, useMemo, useState } from "react";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";

type MermaidDiagramProps = {
  chart: string;
  title?: string;
  enableExport?: boolean;
};

export function MermaidDiagram({ chart, title, enableExport = true }: MermaidDiagramProps) {
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const elementId = useMemo(
    () => `mermaid-${Math.random().toString(36).slice(2, 10)}`,
    []
  );

  useEffect(() => {
    let cancelled = false;

    async function renderChart() {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          theme: "dark",
          securityLevel: "strict",
        });
        const { svg: generatedSvg } = await mermaid.render(elementId, chart);
        if (!cancelled) {
          setSvg(generatedSvg);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Mermaid render failed");
          setSvg("");
        }
      }
    }

    if (chart.trim().length > 0) {
      void renderChart();
    }

    return () => {
      cancelled = true;
    };
  }, [chart, elementId]);

  if (error) {
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-950/40 p-3">
        <p className="text-sm text-red-300">Diagram render error: {error}</p>
      </div>
    );
  }

  const downloadSvg = () => {
    if (!svg) return;
    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "repomind-diagram.svg";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const downloadPng = async () => {
    if (!svg) return;
    const svgBlob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);
    const image = new Image();
    image.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = image.width || 1600;
      canvas.height = image.height || 900;
      const context = canvas.getContext("2d");
      if (!context) return;
      context.fillStyle = "#0B1120";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0);
      canvas.toBlob((blob) => {
        if (!blob) return;
        const pngUrl = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = pngUrl;
        link.download = "repomind-diagram.png";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(pngUrl);
      }, "image/png");
      URL.revokeObjectURL(url);
    };
    image.src = url;
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        {title ? <h4 className="font-medium">{title}</h4> : null}
        {enableExport ? (
          <div className="flex gap-2">
            <Button variant="outline" className="gap-2" onClick={downloadSvg} type="button">
              <Download className="h-4 w-4" />
              SVG
            </Button>
            <Button variant="outline" className="gap-2" onClick={downloadPng} type="button">
              <Download className="h-4 w-4" />
              PNG
            </Button>
          </div>
        ) : null}
      </div>
      <div
        className="overflow-auto rounded-lg border border-white/10 bg-black/30 p-3 [&_svg]:h-auto [&_svg]:max-w-full"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </div>
  );
}
