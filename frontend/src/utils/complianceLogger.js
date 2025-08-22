// src/utils/complianceLogger.js
export const logComplianceResults = (data, source = "Detection") => {
  console.log(`=== ${source.toUpperCase()} COMPLIANCE CHECK ===`);
  console.log("Overall compliant:", data.compliant ? "✅ YES" : "❌ NO");
  console.log("Model used:", data.model_used);
  
  if (data.compliant) {
    console.log("🎉 All clothing items are compliant!");
  } else {
    console.log("⚠️ Non-compliant items detected:");
    data.non_compliant_items.forEach(item => {
      console.log(`   - ${item}`);
    });
  }
  
  console.log("Detected items:", data.clothes_detected.map(d => d.class));
  console.log("==================================");
};