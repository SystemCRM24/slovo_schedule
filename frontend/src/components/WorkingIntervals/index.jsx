import React, {useMemo} from 'react';
import {getWorkingDayFromSchedule, getDatesDiffInMinutes, getWorkingIntervalsFromSchedules} from "../../utils/dates.js";
import WorkingInterval from "../../WorkingInterval/index.jsx";
import {useSpecialistContext} from "../../contexts/Specialist/provider.jsx";
import useSchedules from "../../hooks/useSchedules.js";

const WorkingIntervals = () => {
    const {schedule, workSchedule, generalWorkSchedule}
        = useSchedules();
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
            return getWorkingIntervalsFromSchedules(schedule, workSchedule, workingDay.start, workingDay.end);
        },
        [schedule, workSchedule, generalWorkSchedule]
    );
    return (
        <div className={'h-100 w-100'}>
            {intervals.map(interval => {
                const intervalDuration = getDatesDiffInMinutes(interval.start, interval.end);
                const percentOfWorkingDay = intervalDuration / workingDayDurationMinutes * 100;
                return (
                    <WorkingInterval
                        startDt={interval.start}
                        endDt={interval.end}
                        percentOfWorkingDay={percentOfWorkingDay}
                        patientName={interval?.patient?.name}
                        patientType={interval?.patient?.type}
                        status={interval.status}
                        key={`${interval.start}_${interval.end}_${specialistId}_working_interval_elem`}
                    />
                );
            })}
        </div>
    );
}

export default React.memo(WorkingIntervals);