import { FC } from 'react'

interface DPadProps {
    onUp?: () => void
    onDown?: () => void
    onLeft?: () => void
    onRight?: () => void
    onCenter?: () => void
}

export const DPad: FC<DPadProps> = ({
    onUp,
    onDown,
    onLeft,
    onRight,
    onCenter,
}) => {
    const buttonClass =
        'w-12 h-12 border border-slate-600 rounded-lg bg-slate-700 text-cyan-400 text-lg flex items-center justify-center cursor-pointer transition-all duration-200 shadow-md hover:shadow-lg hover:shadow-cyan-500/30 hover:-translate-y-0.5 hover:border-cyan-400 active:shadow-sm active:translate-y-0'

    return (
        <div className="flex flex-col items-center gap-2 p-4 bg-slate-800 border border-slate-700 rounded-lg shadow-lg shadow-cyan-500/10 w-fit">
            <button
                className={buttonClass}
                onClick={onUp}
                aria-label="Up"
            >
                ▲
            </button>

            <div className="flex gap-2 items-center justify-center">
                <button
                    className={`${buttonClass} text-base`}
                    onClick={onLeft}
                    aria-label="Left"
                >
                    ◄
                </button>

                <button
                    className="w-12 h-12 border-none rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 text-white text-2xl flex items-center justify-center cursor-pointer transition-all duration-200 shadow-md hover:shadow-lg hover:shadow-cyan-400/40 hover:-translate-y-0.5 hover:from-cyan-400 hover:to-blue-500 active:shadow-sm active:translate-y-0"
                    onClick={onCenter}
                    aria-label="Stop"
                >
                    ⏹
                </button>

                <button
                    className={buttonClass}
                    onClick={onRight}
                    aria-label="Right"
                >
                    ►
                </button>
            </div>

            <button
                className={buttonClass}
                onClick={onDown}
                aria-label="Down"
            >
                ▼
            </button>
        </div>
    )
}
