import React, {useMemo} from 'react';
import {useWorkScheduleContext} from "../../contexts/WorkSchedule/provider.jsx";
import {getWorkingDayFromSchedule, getDatesDiffInMinutes, getWorkingIntervalsFromSchedules} from "../../utils/dates.js";
import WorkingInterval from "../../WorkingInterval/index.jsx";

const WorkingIntervals = ({schedule, workSchedule, specialist}) => {
    const [generalWorkSchedule] = useWorkScheduleContext();
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
            return getWorkingIntervalsFromSchedules(schedule, workSchedule);
        },
        [schedule, workSchedule]
    );
    console.log(intervals);
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
                        key={`${interval.start}_${interval.end}_${specialist}`}
                    />
                );
            })}
        </div>
    );
}

export default WorkingIntervals;