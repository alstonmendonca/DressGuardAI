import React, { useState, useEffect } from 'react';
import { XIcon } from './Icons';

export default function Notification({ message, type = 'warning', duration = 3000, onClose }) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => {
            setVisible(false);
            if (onClose) onClose();
        }, duration);

        return () => clearTimeout(timer);
    }, [duration, onClose]);

    if (!visible) return null;

    const typeStyles = {
        warning: 'bg-yellow-900 border-yellow-500 text-yellow-100',
        error: 'bg-red-900 border-red-500 text-red-100',
        info: 'bg-blue-900 border-blue-500 text-blue-100',
        success: 'bg-green-900 border-green-500 text-green-100'
    };

    const icons = {
        warning: '⚠️',
        error: '❌',
        info: 'ℹ️',
        success: '✓'
    };

    return (
        <div className={`fixed top-4 right-4 z-50 ${typeStyles[type]} border-2 rounded-lg shadow-lg p-4 min-w-[300px] max-w-[400px] animate-slide-in`}>
            <div className="flex items-start gap-3">
                <span className="text-2xl">{icons[type]}</span>
                <div className="flex-1">
                    <p className="font-semibold text-sm">{message}</p>
                </div>
                <button
                    onClick={() => {
                        setVisible(false);
                        if (onClose) onClose();
                    }}
                    className="text-white hover:opacity-70 transition"
                >
                    <XIcon className="w-5 h-5" />
                </button>
            </div>
        </div>
    );
}
