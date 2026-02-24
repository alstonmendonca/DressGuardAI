import React, { useState, useEffect } from "react";
import { XIcon, AlertIcon, CalendarIcon } from "./Icons";

export default function WhatsAppAlert({ isOpen, onClose }) {
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [selectedModel, setSelectedModel] = useState('');
    const [availableDates, setAvailableDates] = useState([]);
    const [availableModels, setAvailableModels] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [whatsappStatus, setWhatsappStatus] = useState({ enabled: false, configured: false });

    useEffect(() => {
        if (isOpen) {
            fetchAvailableDates();
            fetchAvailableModels();
            checkWhatsappStatus();
        }
    }, [isOpen]);

    const fetchAvailableModels = async () => {
        try {
            const response = await fetch("/api/dashboard/models/");
            if (response.ok) {
                const data = await response.json();
                setAvailableModels(data.models);
                // Set first model as default if available
                if (data.models.length > 0 && !selectedModel) {
                    setSelectedModel(data.models[0]);
                }
            }
        } catch (err) {
            console.error("Error fetching models:", err);
        }
    };

    const checkWhatsappStatus = async () => {
        try {
            const response = await fetch("/dashboard/whatsapp/status/");
            if (response.ok) {
                const data = await response.json();
                setWhatsappStatus(data);
            }
        } catch (err) {
            console.error("Error checking WhatsApp status:", err);
        }
    };

    const fetchAvailableDates = async () => {
        try {
            const response = await fetch("/api/dashboard/dates/");
            if (response.ok) {
                const data = await response.json();
                setAvailableDates(data.dates);
                // Set selected date to first available if current date has no logs
                if (data.dates.length > 0 && !data.dates.includes(selectedDate)) {
                    setSelectedDate(data.dates[0]);
                }
            }
        } catch (err) {
            console.error("Error fetching dates:", err);
        }
    };

    const handleDateChange = (e) => {
        setSelectedDate(e.target.value);
        setError(null);
    };

    const handleModelChange = (e) => {
        setSelectedModel(e.target.value);
        setError(null);
    };

    const handleSendWhatsApp = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch("/dashboard/send-whatsapp/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ 
                    date: selectedDate,
                    model: (selectedModel && selectedModel !== 'all' && selectedModel !== '') ? selectedModel : null
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to send WhatsApp notification');
            }

            // Show success message
            const successMsg = `✓ WhatsApp Alert sent successfully!\n\nDate: ${data.date}\nModel: ${selectedModel}\nViolations: ${data.violation_count}\nRecipients: ${data.successful_sends}/${data.total_recipients}`;
            alert(successMsg);
            
            // Close modal on success
            onClose();

        } catch (err) {
            console.error("Error sending WhatsApp:", err);
            setError(err.message || 'Failed to send WhatsApp notification');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
            <div className="bg-green-950 border-2 border-green-500 rounded-lg w-full max-w-md">
                {/* Header */}
                <div className="flex justify-between items-center p-4 border-b border-green-500">
                    <div className="flex items-center gap-2">
                        <AlertIcon className="w-6 h-6 text-green-300" />
                        <h2 className="text-xl font-bold text-green-300">Send WhatsApp Alert</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-green-400 hover:text-green-200 transition"
                    >
                        <XIcon className="w-6 h-6" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">
                    {whatsappStatus.enabled && whatsappStatus.configured ? (
                        <>
                            <p className="text-green-300 text-sm mb-4">
                                Generate a report and send it via WhatsApp with violation details.
                            </p>

                            {/* Date Selection */}
                            <div className="mb-4">
                                <label className="block text-green-300 text-sm font-semibold mb-2">
                                    Select Date:
                                </label>
                                
                                {/* Manual Date Picker */}
                                <div className="flex items-center gap-2 mb-3">
                                    <CalendarIcon className="w-5 h-5 text-green-400" />
                                    <input
                                        type="date"
                                        value={selectedDate}
                                        onChange={handleDateChange}
                                        className="flex-1 bg-black border border-green-600 text-green-200 px-3 py-2 rounded focus:outline-none focus:border-green-400"
                                    />
                                </div>

                                {/* Quick Date Selector */}
                                {availableDates.length > 0 && (
                                    <div>
                                        <label className="block text-green-400 text-xs mb-1">
                                            Or choose from available dates:
                                        </label>
                                        <select
                                            value={selectedDate}
                                            onChange={handleDateChange}
                                            className="w-full bg-black border border-green-600 text-green-200 px-3 py-2 rounded focus:outline-none focus:border-green-400"
                                        >
                                            {availableDates.map(date => (
                                                <option key={date} value={date}>
                                                    {date === new Date().toISOString().split('T')[0] ? `${date} (Today)` : date}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                )}

                                {availableDates.length === 0 && (
                                    <p className="text-yellow-400 text-xs mt-2">
                                        No violation logs found. Start detecting to send alerts.
                                    </p>
                                )}
                            </div>

                            {/* Model Selection */}
                            <div className="mb-6">
                                <label className="block text-green-300 text-sm font-semibold mb-2">
                                    Select Model:
                                </label>
                                <select
                                    value={selectedModel}
                                    onChange={handleModelChange}
                                    className="w-full bg-black border border-green-600 text-green-200 px-3 py-2 rounded focus:outline-none focus:border-green-400"
                                >
                                    {availableModels.map(model => (
                                        <option key={model} value={model}>
                                            {model}
                                        </option>
                                    ))}
                                </select>
                                <p className="text-green-500 text-xs mt-1">
                                    Alert will include violations from the selected model only
                                </p>
                            </div>

                            {/* Error Message */}
                            {error && (
                                <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-500 rounded">
                                    <p className="text-red-200 text-sm">{error}</p>
                                </div>
                            )}

                            {/* Alert Details */}
                            <div className="bg-green-900 bg-opacity-30 border border-green-700 rounded p-3 mb-6">
                                <h3 className="text-green-300 text-sm font-semibold mb-2">WhatsApp message will include:</h3>
                                <ul className="text-green-400 text-xs space-y-1">
                                    <li>• Report date and model used</li>
                                    <li>• Total violation count</li>
                                    <li>• Excel report with images attached</li>
                                    <li>• Student details and timestamps</li>
                                    <li>• Non-compliant items list</li>
                                    <li>• License plates (if applicable)</li>
                                </ul>
                                {selectedModel && (
                                    <div className="mt-2 pt-2 border-t border-green-700">
                                        <p className="text-yellow-400 text-xs">
                                            ⚠️ Filtering by: <span className="font-semibold">{selectedModel}</span>
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* Action Buttons */}
                            <div className="flex gap-3">
                                <button
                                    onClick={handleSendWhatsApp}
                                    disabled={loading || availableDates.length === 0}
                                    className={`flex-1 py-2 px-4 rounded font-semibold flex items-center justify-center gap-2 transition ${
                                        loading || availableDates.length === 0
                                            ? 'bg-gray-700 border border-gray-600 text-gray-400 cursor-not-allowed'
                                            : 'bg-green-600 border border-green-400 text-white hover:bg-green-500'
                                    }`}
                                >
                                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                                    </svg>
                                    {loading ? 'Sending via WhatsApp...' : 'Send Alert via WhatsApp'}
                                </button>
                                
                                <button
                                    onClick={onClose}
                                    disabled={loading}
                                    className="px-4 py-2 bg-black border border-green-600 text-green-300 rounded hover:bg-green-900 transition disabled:opacity-50"
                                >
                                    Cancel
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="text-center py-8">
                            <AlertIcon className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
                            <h3 className="text-yellow-400 font-semibold mb-2">WhatsApp Not Configured</h3>
                            <p className="text-green-300 text-sm mb-4">
                                WhatsApp service is not properly configured.
                            </p>
                            <div className="bg-green-900 bg-opacity-30 border border-green-700 rounded p-4 text-left">
                                <p className="text-green-400 text-xs mb-2">To enable WhatsApp alerts:</p>
                                <ol className="text-green-400 text-xs space-y-1 list-decimal list-inside">
                                    <li>Start WhatsApp service in whatsapp-service folder</li>
                                    <li>Scan QR code with your phone</li>
                                    <li>Configure recipients in config.py</li>
                                </ol>
                            </div>
                            <button
                                onClick={onClose}
                                className="mt-4 px-4 py-2 bg-black border border-green-600 text-green-300 rounded hover:bg-green-900 transition"
                            >
                                Close
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
