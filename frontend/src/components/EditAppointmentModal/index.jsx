import { useCallback, useMemo } from "react";
import CustomModal from "../ui/Modal";
import { Button } from "react-bootstrap";

import { useDayContext } from "../../contexts/Day/provider";
import { useScheduleContext } from "../../contexts/Schedule/provider";
import { useSpecialistContext } from "../../contexts/Specialist/provider";
import useSchedules from "../../hooks/useSchedules";


const EditAppointmentModal = ({show, setShow, startDt, endDt}) => {
    const specialist = useSpecialistContext();
    const [schedule, setSchedule] = useScheduleContext();
    const {generalSchedule, setGeneralSchedule} = useSchedules();
    const day = useDayContext();

    const [record, recordIndex] = useMemo(
        () => {
            let index = -1;
            for ( const record of schedule[specialist][day] ) {
                index++;
                if ( record.start == startDt && record.end == endDt ) {
                    return [record, index];
                }
            }
            return [{}, -1];
        },
        [specialist, schedule, day, startDt, endDt]
    )

    const onDeleteBtnClick = useCallback(
        () => {
            setShow(false);
            const schedulesOfDay = schedule[specialist][day];
            schedulesOfDay.splice(recordIndex, 1);
            console.log(schedule);
            setSchedule(schedule);
            // setGeneralSchedule({
            //     ...generalSchedule,
                
            // })
        },
        [setShow, day, schedule, specialist, recordIndex, setSchedule]
    );

    return (
        <CustomModal
            show={show}
            handleClose={()=>setShow(false)}
            title={'Редактирование'}
        >
            <Button
                variant="danger"
                onClick={onDeleteBtnClick}
            >
                Удалить
            </Button>
        </CustomModal>
    );
}

export default EditAppointmentModal;