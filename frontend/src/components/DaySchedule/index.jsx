import WorkingIntervals from "../WorkingIntervals/index.jsx";
import EmptyWorkSchedule from "../EmptyWorkSchedule/index.jsx";
import React from "react";
import {useWorkScheduleContext} from "../../contexts/WorkSchedule/provider.jsx";
import {useScheduleContext} from "../../contexts/Schedule/provider.jsx";

const DaySchedule = ({specialist, date}) => {
    const [generalWorkSchedule] = useWorkScheduleContext();
    const [generalSchedule] = useScheduleContext()
    const workSchedule = generalWorkSchedule?.[specialist]?.[date] || [];
    const schedule = generalSchedule?.[specialist]?.[date] || [];
    return (
        <td className={'p-0'} style={{height: "inherit"}}>
            <div className={'d-flex flex-column align-items-center justify-content-center h-100 w-100'}>
                {
                    workSchedule.length > 0 ?
                        <WorkingIntervals schedule={schedule} workSchedule={workSchedule}/>
                        :
                        <EmptyWorkSchedule specialist={specialist}/>
                }
            </div>
        </td>
    );
}

export default React.memo(DaySchedule);