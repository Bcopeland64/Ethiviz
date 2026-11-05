import React from 'react';

export interface DimensionMapFinding {
  dimension: string;
  score?: number;
  evidence?: string;
}

interface DimensionMapViewProps {
  findings?: DimensionMapFinding[];
}

const DimensionMapView: React.FC<DimensionMapViewProps> = ({ findings = [] }) => {
  return (
    <section aria-label="Dimension map" className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-600">Dimension Map</h3>
      {findings.length === 0 ? (
        <p className="text-sm text-slate-500">No dimension map data available for this result.</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {findings.map((finding, index) => (
            <div key={`${finding.dimension}-${index}`} className="rounded-md border border-slate-200 bg-slate-50 p-3">
              <div className="mb-1 flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-slate-700">{finding.dimension}</span>
                {typeof finding.score === 'number' && (
                  <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700">
                    {finding.score.toFixed(2)}
                  </span>
                )}
              </div>
              {finding.evidence && <p className="text-xs text-slate-600">{finding.evidence}</p>}
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

export default DimensionMapView;
