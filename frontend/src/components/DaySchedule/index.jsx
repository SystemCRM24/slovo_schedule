import WorkingIntervals from "../WorkingIntervals/index.jsx";
import EmptyWorkSchedule from "../EmptyWorkSchedule/index.jsx";
import React from "react";
import useSchedules from "../../hooks/useSchedules.js";

const DaySchedule = () => {
    const {workSchedule} = useSchedules();
    return (
        <td className={'p-0'} >
            <div>
                {
                    workSchedule?.intervals.length > 0 ?
                        <WorkingIntervals />
                        :
                        <EmptyWorkSchedule />
                }
            </div>
        </td>
    );
}

export default React.memo(DaySchedule);