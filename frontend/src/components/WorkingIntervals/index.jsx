import React, {useMemo} from 'react';
import {getWorkingDayFromSchedule, getDatesDiffInMinutes, getWorkingIntervalsFromSchedules} from "../../utils/dates.js";
import WorkingInterval from "../WorkingInterval/index.jsx";
import {useSpecialistContext} from "../../contexts/Specialist/provider.jsx";
import useSchedules from "../../hooks/useSchedules.js";

const WorkingIntervals = () => {
    const {schedule, workSchedule, generalWorkSchedule} = useSchedules();
    const specialistId = useSpecialistContext();

    const workingDayDurationMinutes = useMemo(
        () => {
            const workingDay = getWorkingDayFromSchedule(generalWorkSchedule);
            const workingDayStart = new Date();
            const workingDayEnd = new Date();
            workingDayStart.setHours(workingDay.start.hours, workingDay.start.minutes);
            workingDayEnd.setHours(workingDay.end.hours, workingDay.end.minutes);
            return getDatesDiffInMinutes(workingDayStart, workingDayEnd);
        },
        [generalWorkSchedule]
    );
    
    const intervals = useMemo(
        () => {
            const workingDay = getWorkingDayFromSchedule(generalWorkSchedule);
            const result = getWorkingIntervalsFromSchedules(schedule, workSchedule.intervals, workingDay.start, workingDay.end);
            for ( const appointment of schedule ) {
                let index = 0;
                for ( let i=0; i < result.length; i++) {
                    const interval = result[i];
                    if ( interval?.id === appointment.id || appointment.id === undefined) {   // Нам не нужно вставлять дубли
                        index = -1;
                        break;
                    }
                    if ( appointment.start.getTime() >= interval.start.getTime() ) {
                        index = i;
                    }
                }
                if ( index === -1 ) {
                    continue;
                }
                result.splice(index, 0, appointment);
            }
            return [...result];
        },
        [schedule, workSchedule, generalWorkSchedule]
    );

    const renderedIntervals = useMemo(
        () => {
            const result = [];
            const keys = new Set();
            for ( const interval of intervals ) {
                const key = `${interval.start}_${interval.end}_${specialistId}_working_interval_elem`;
                if ( keys.has(key) ) {
                    continue;
                } else {
                    keys.add(key)
                }
                const intervalDuration = getDatesDiffInMinutes(interval.start, interval.end);
                const percentOfWorkingDay = intervalDuration / workingDayDurationMinutes * 100;
                result.push(
                    <WorkingInterval
                        id={interval?.id}
                        startDt={interval.start}
                        endDt={interval.end}
                        percentOfWorkingDay={percentOfWorkingDay}
                        patientId={interval?.patient?.id}
                        patientType={interval?.patient?.type}
                        status={interval.status}
                        key={`${interval.start}_${interval.end}_${specialistId}_working_interval_elem`}
                    />
                );
            }
            return result;
        },
        [intervals]
    );

    return (<div className={'h-100 w-100'}>{renderedIntervals}</div>);
}

export default WorkingIntervals;