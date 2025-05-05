import { useCallback, useMemo } from "react";
import CustomModal from "../ui/Modal";
import { Button } from "react-bootstrap";

import { useDayContext } from "../../contexts/Day/provider";
import useSchedules from "../../hooks/useSchedules";
import useSpecialist from "../../hooks/useSpecialist.js";


const EditAppointmentModal = ({show, setShow, startDt, endDt}) => {
    const {specialistId, specialist} = useSpecialist();
    const {schedule, generalSchedule, setGeneralSchedule} = useSchedules();
    const day = useDayContext();

    const [record, recordIndex] = useMemo(
        () => {
            let index = -1;
            for ( const record of schedule ) {
                index++;
                if ( record.start.getTime() === startDt.getTime() && record.end.getTime() === endDt.getTime() ) {
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
            console.log(recordIndex);
            const newSchedule = schedule.filter((item, index) => index !== recordIndex);
            console.log(newSchedule);
            setGeneralSchedule({
                ...generalSchedule,
                [specialistId]: {
                    ...generalSchedule[specialistId],
                    [day]: newSchedule,
                }
            })
        },
        [setShow, recordIndex, schedule, setGeneralSchedule, generalSchedule, specialistId]
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