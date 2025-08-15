// components/DetectionList.jsx
import React from "react";

export default function DetectionList({ detections }) {
  return (
    <div className="row-span-1 bg-green-950 p-4 rounded shadow-lg text-left text-sm h-full flex flex-col">
      <h2 className="text-xl font-bold border-b border-green-400 mb-2">
        Detected Items:
      </h2>

      {detections.length > 0 ? (
        <ul className="list-disc pl-6 space-y-1 flex-1">
          {detections.map((det, index) => (
            <li key={index}>
              <span className="font-bold">{det.class}</span> –{" "}
              {det.confidence.toFixed(2)}%
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-green-600 italic text-center py-4 flex-1 flex items-center justify-center">
          No items detected
        </p>
      )}
    </div>
  );
}
