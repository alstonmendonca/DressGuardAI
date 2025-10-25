// components/DetectionList.jsx
import React, { memo } from "react";
import { CheckIcon, XIcon } from "./Icons";

const DetectionListItem = memo(({ det, compliant }) => (
  <li className={`p-2 rounded border ${
    compliant 
      ? 'border-green-500 bg-green-900/20' 
      : 'border-red-500 bg-red-900/20'
  }`}>
    <div className="flex justify-between items-center">
      <span className="font-bold">{det.class}</span>
      <span className="text-xs opacity-75">{det.confidence.toFixed(2)}</span>
    </div>
    <div className={`text-xs mt-1 flex items-center gap-1 ${
      compliant ? 'text-green-400' : 'text-red-400'
    }`}>
      {compliant ? (
        <>
          <CheckIcon className="w-3 h-3" /> Compliant
        </>
      ) : (
        <>
          <XIcon className="w-3 h-3" /> Non-Compliant
        </>
      )}
    </div>
  </li>
));

function DetectionList({ detections, complianceInfo }) {
  const isItemCompliant = (itemName) => {
    return !complianceInfo.nonCompliantItems.includes(itemName);
  };

  // Filter detections to only include those with confidence > 0.5
  const filteredDetections = detections.filter(det => det.confidence > 0.5);

  return (
    <div className="row-span-1 bg-green-950 p-4 rounded shadow-lg text-left text-sm h-full flex flex-col">
      <h2 className="text-xl font-bold border-b border-green-400 mb-2">
        Detected Items:
      </h2>

      {filteredDetections.length > 0 ? (
        <ul className="space-y-2 flex-1">
          {filteredDetections.map((det, index) => (
            <DetectionListItem 
              key={`${det.class}-${det.confidence}-${index}`}
              det={det}
              compliant={isItemCompliant(det.class)}
            />
          ))}
        </ul>
      ) : (
        <p className="text-green-600 italic text-center py-4 flex-1 flex items-center justify-center">
          No items detected
        </p>
      )}
      {/* Overall compliance status */}
      {filteredDetections.length > 0 && (
        <div className={`mt-4 p-3 rounded border ${
          complianceInfo.isCompliant 
            ? 'border-green-500 bg-green-900/30' 
            : 'border-red-500 bg-red-900/30'
        }`}>
          <h3 className="font-bold mb-1">Overall Status:</h3>
          <p className={`flex items-center gap-2 ${complianceInfo.isCompliant ? 'text-green-400' : 'text-red-400'}`}>
            {complianceInfo.isCompliant ? (
              <>
                <CheckIcon className="w-4 h-4" /> All items compliant
              </>
            ) : (
              <>
                <XIcon className="w-4 h-4" /> {complianceInfo.nonCompliantItems.length} non-compliant item(s)
              </>
            )}
          </p>
          {complianceInfo.nonCompliantItems.length > 0 && (
            <div className="text-xs mt-2">
              <span className="font-semibold">Non-compliant:</span>
              <ul className="list-disc list-inside mt-1">
                {complianceInfo.nonCompliantItems.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      
    </div>
  );
}

export default memo(DetectionList);