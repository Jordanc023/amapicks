import React from 'react';
import { Loader2 } from 'lucide-react';

const Button = ({
    children,
    variant = 'primary',
    className = '',
    isLoading = false,
    disabled = false,
    ...props
}) => {
    const baseStyles = "px-6 py-2.5 rounded-lg font-medium transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed tracking-wide text-sm uppercase relative overflow-hidden group";

    const variants = {
        primary: "bg-gold-500 text-dark-950 hover:bg-gold-400 shadow-[0_0_15px_rgba(212,175,55,0.3)] hover:shadow-[0_0_25px_rgba(212,175,55,0.5)] border border-gold-400/50",
        secondary: "bg-white/5 hover:bg-white/10 text-gold-100 border border-white/10 hover:border-gold-500/30 backdrop-blur-md",
        outline: "bg-transparent border border-gold-500/30 text-gold-400 hover:text-gold-300 hover:border-gold-400 hover:bg-gold-500/5",
        ghost: "bg-transparent hover:bg-white/5 text-gray-400 hover:text-gold-200"
    };

    return (
        <button
            className={`${baseStyles} ${variants[variant]} ${className}`}
            disabled={disabled || isLoading}
            {...props}
        >
            {/* Shine Effect */}
            <div className="absolute inset-0 -translate-x-full group-hover:animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent z-10 pointer-events-none" />

            {isLoading && <Loader2 className="w-4 h-4 animate-spin relative z-20" />}
            <span className="relative z-20">{children}</span>
        </button>
    );
};

export default Button;
