import React, { useCallback, useMemo } from "react";
import StatisticsContext from "./context";


class Point{
    constructor() {
        this.scheduleDuration = 0;
        this.appointmentDuration = 0;
    }

    get percent() {
        let result = (this.appointmentDuration / this.scheduleDuration * 100).toFixed(1);
        if ( result.endsWith('0') ) {
            result = result.split('.')[0];
        }
        return `${result}%`;
    }
}


export function StatisticsContextProvider({ children, schedules, appointments }) {
    const [totals, byDays] = useMemo(
        () => {
            let totals = null;
            let byDays = null;
            if ( schedules && appointments ) {
                totals = {};
                byDays = {};
                // Пробегаемся по схедулям
                for ( const [specialist, specialistSchedules] of Object.entries(schedules) ) {
                    for ( const [date, data] of Object.entries(specialistSchedules) ) {
                        let duration = 0;
                        for ( const interval of data.intervals ) {
                            duration += interval.end.getTime() - interval.start.getTime();
                        }
                        // Обновляем Тоталс
                        const specDataTotal = totals[specialist] ??= new Point();
                        specDataTotal.scheduleDuration += duration;
                        // Обновляем байДейс
                        const specDataByDays = byDays[specialist] ??= {};
                        const dayData = specDataByDays[date] ??= new Point();
                        dayData.scheduleDuration += duration;
                    }
                }
                // Пробегаемся по занятиям
                for ( const [specialist, specialistAppointments] of Object.entries(appointments) ) {
                    for ( const [date, data] of Object.entries(specialistAppointments) ) {
                        let duration = 0;
                        for ( const appointment of data ) {
                            duration += appointment.end.getTime() - appointment.start.getTime();
                        }
                        // Обновляем Тоталс
                        const specDataTotal = totals[specialist] ??= new Point();
                        specDataTotal.appointmentDuration += duration;
                        // Обновляем байДейс
                        const specDataByDays = byDays[specialist] ??= {};
                        const dayData = specDataByDays[date] ??= new Point();
                        dayData.appointmentDuration += duration;
                    }
                }
            }
            return [totals, byDays]
        },
        [schedules, appointments]
    );

    const getDayStat = useCallback(
        (specialist, dayDate) => {
            let result = 'loading';
            if (byDays !== null) {
                const record = byDays?.[specialist]?.[dayDate];
                result = record ? record.percent : 'Нет данных.';
            }
            return result;
        },
        [byDays]
    );

    const getTotalStat = useCallback(
        (specialist) => {
            let result = null;
            if (totals !== null) {
                const record = totals[specialist];
                result = record ? record.percent : '0%';
            }
            return result;
        },
        [totals]
    )

    return (
        <StatisticsContext.Provider
            value={{
                getDayStat,
                getTotalStat
            }}
        >
            {children}
        </StatisticsContext.Provider>
    )
}


function useStatisticsContext() {
    const context = React.useContext(StatisticsContext);
    if (!context) throw new Error('Use context within provider!');
    return context;
}

export default useStatisticsContext;
