import React, {useCallback, useMemo} from 'react';
import CustomModal from "../ui/Modal/index.jsx";
import useSchedules from "../../hooks/useSchedules.js";
import {useSpecialistContext} from "../../contexts/Specialist/provider.jsx";
import {useDayContext} from "../../contexts/Day/provider.jsx";
import {getTimeStringFromDate} from "../../utils/dates.js";

const EditWorkScheduleModal = ({show, setShow, startDt, endDt}) => {
    const {
        generalSchedule,
        generalWorkSchedule,
        setGeneralSchedule,
        setGeneralWorkSchedule,
        schedule,
        workSchedule
    } = useSchedules();
    const specialistId = useSpecialistContext();
    const date = useDayContext();
    const dayOfWeek = date.toLocaleString('ru-RU', {weekday: 'long'});
    const dateString = date.toLocaleDateString();
    const findIntervalPredicate = useCallback((interval) => {
        return interval.start.getTime() <= startDt.getTime() && interval.end.getTime() >= endDt.getTime()
    }, [startDt, endDt]);
    const [realInterval, realIntervalIndex] = useMemo(() => {
       return [workSchedule.find(findIntervalPredicate),workSchedule.findIndex(findIntervalPredicate)]
    }, [workSchedule, findIntervalPredicate]);
    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={`${specialistId} - ${dayOfWeek} ${dateString} ${getTimeStringFromDate(startDt)} - ${getTimeStringFromDate(endDt)}`}
        >

        </CustomModal>
    );
};

export default React.memo(EditWorkScheduleModal);