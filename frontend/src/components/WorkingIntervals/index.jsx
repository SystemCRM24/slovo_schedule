import React, {useMemo} from 'react';
import {useWorkScheduleContext} from "../../contexts/WorkSchedule/provider.jsx";
import {getWorkingDayFromSchedule, getDatesDiffInMinutes} from "../../utils/dates.js";

const WorkingIntervals = ({schedule, workSchedule, workingDayDurationMinutes}) => {
    console.log(schedule, workSchedule)
    const [generalWorkSchedule] = useWorkScheduleContext();
    const workingDayDuration = useMemo(() => {
        console.log('memo call');
        const workingDay = getWorkingDayFromSchedule(generalWorkSchedule);
        console.log(workingDay);
        const workingDayStart = new Date();
        const workingDayEnd = new Date();
        workingDayStart.setHours(workingDay.start.hours, workingDay.start.minutes);
        workingDayEnd.setHours(workingDay.end.hours, workingDay.end.minutes);
        return getDatesDiffInMinutes(workingDayStart, workingDayEnd);
    }, [generalWorkSchedule]);
    return (
        <div className={'h-100 w-100'}>
            Тут будут занятия {workingDayDuration}
        </div>
    );
}

export default WorkingIntervals;