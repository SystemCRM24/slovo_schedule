import React, { useCallback, useContext, useMemo, useState } from "react";
import CustomModal from "../ui/Modal/index.jsx";
import { Button, FormControl, FormSelect, InputGroup } from "react-bootstrap";

import { useDayContext } from "../../contexts/Day/provider.jsx";
import { AppContext } from "../../contexts/App/context.js";
import { useAllSpecialistsContext } from "../../contexts/AllSpecialists/provider.jsx";
import useSchedules from "../../hooks/useSchedules.js";
import useSpecialist from "../../hooks/useSpecialist.js";
import { getDateWithTime, getISODate, getTimeStringFromDate, isIntervalValid, isNewScheduleIntervalValid } from "../../utils/dates.js";
import { useChildrenContext } from "../../contexts/Children/provider.jsx";
import apiClient, { constants } from "../../api/index.js";

const EditClientInfoModal = ({ id, show, setShow, startDt, endDt, patientId, patientType, status, oldpatientId }) => {
    const { specialistId, specialist } = useSpecialist();
    const specialists = useAllSpecialistsContext();
    const { dates, setDates } = useContext(AppContext)
    const [appointment, setAppointment] = useState({
        id: id,
        status: status,
        patientId: patientId,
        patientType: patientType,
        start: startDt,
        end: endDt,
        specialist: specialistId,
    });
    const { schedule, generalSchedule, setGeneralSchedule, workSchedule } = useSchedules();
    const patients = useChildrenContext();
    const patientName = useMemo(() => patients?.[patientId], [patientId, patients]);
    const day = useDayContext();
    const children = useChildrenContext();
    const dayOfWeek = day.toLocaleString('ru-RU', { weekday: 'long' });
    const dateString = day.toLocaleDateString();
    const [workDay, setWorkDay] = useState(day);

    const [record, recordIndex] = useMemo(() => {
        let index = -1;
        for (const record of schedule) {
            index++;
            if (record.start.getTime() === startDt.getTime() && record.end.getTime() === endDt.getTime()) {
                return [record, index];
            }
        }
        return [{}, -1];
    }, [schedule, startDt, endDt]);
    const scheduleWithoutCurrentElem = useMemo(() => {
        return schedule.filter((value, index) => index !== recordIndex);
    }, [recordIndex, schedule]);

    const onSubmit = async () => {
        const newRecord = {
            id: appointment.id,
            start: appointment.start,
            end: appointment.end,
            specialist: appointment.specialist,
            patient: appointment.patientId,
            code: appointment.patientType,
            status: appointment.status,
            old_patient: oldpatientId,
        };
        const result = await apiClient.updateAppointment(id, newRecord);
        if (result) {
            const newSchedule = schedule.filter((item, index) => index !== recordIndex);
            const updatedSchedules = await apiClient.getSchedules(workDay, workDay);
            setGeneralSchedule(updatedSchedules);

            if (appointment.specialist === specialistId) {
                setGeneralSchedule({
                    ...generalSchedule,
                    [specialistId]: {
                        ...generalSchedule[specialistId],
                        [getISODate(workDay)]: [
                            ...newSchedule,
                            {
                                ...newRecord,
                                patient: {
                                    id: appointment.patientId,
                                    type: appointment.patientType,
                                },
                            },
                        ],
                    },
                });
            } else {
                const newSpecialistSchedule = generalSchedule[appointment.specialist] || {};
                setGeneralSchedule({
                    ...generalSchedule,
                    [specialistId]: {
                        ...generalSchedule[specialistId],
                        [getISODate(workDay)]: newSchedule,
                    },
                    [appointment.specialist]: {
                        ...newSpecialistSchedule,
                        [getISODate(workDay)]: [
                            ...(newSpecialistSchedule[getISODate(workDay)] || []),
                            {
                                ...newRecord,
                                patient: {
                                    id: appointment.patientId,
                                    type: appointment.patientType,
                                },
                            },
                        ],
                    },
                });
            }
            const newDates = { fromDate: new Date(dates.fromDate), toDate: new Date(dates.toDate) };
            setDates(newDates);
            setShow(false);
        }
    };
    const handleDateInputChange = async (e) => {
        const newDate = new Date(e.target.value);
        if (!isNaN(newDate.getTime())) {
            const hours = appointment.start.getHours();
            const minutes = appointment.start.getMinutes();
            const newStart = getDateWithTime(newDate, hours, minutes);
            const duration = (appointment.end - appointment.start) / (1000 * 60);
            const newEnd = new Date(newStart.getTime() + duration * 60 * 1000);
            await onChange('start', newStart);
            await onChange('end', newEnd);
            setWorkDay(newDate);
        }
    };
    const handleInputChange = async (e) => {
        const { name, value } = e.target;
        let newValue;
        if (['start', 'end'].includes(name)) {
            const [hoursString, minutesString] = value.split(':');
            const hours = parseInt(hoursString);
            const minutes = parseInt(minutesString);
            newValue = getDateWithTime(workDay, hours, minutes);
        } else {
            newValue = value;
        }
        await onChange(name, newValue);
    };
    const onChange = async (attrName, value) => {
        setAppointment((prev) => ({ ...prev, [attrName]: value }));
    };

    return (
        <CustomModal
            show={show}
            handleClose={() => setShow(false)}
            title={`Изменить параметры`}
            primaryBtnDisabled={!workDay}
            handlePrimaryBtnClick={onSubmit}
            primaryBtnText={'Сохранить'}
        >
            <div className="d-flex flex-column align-items-center justify-content-center w-100 h-100 gap-2">
                <label>Дата занятия</label>
                <InputGroup hasValidation>
                    <FormControl
                        type={'date'}
                        value={getISODate(workDay)}
                        name={'day'}
                        onChange={async (e) => {
                            await handleDateInputChange(e);
                        }}
                        style={{ textAlign: "center" }}
                        required
                        isInvalid={
                            !workDay
                            // (!!appointment.start && !isNewScheduleIntervalValid(appointment, scheduleWithoutCurrentElem, scheduleWithoutCurrentElem, workSchedule.intervals))
                        }
                    /> 
                </InputGroup>
                <label>Исполнитель</label>
                <InputGroup hasValidation>
                    <FormSelect
                        name={'specialist'}
                        isInvalid={['', null, undefined].includes(appointment.specialist)}
                        onChange={async (e) => {
                            await handleInputChange(e);
                        }}
                        value={appointment.specialist}
                    >
                        <option value="">Выберите специалиста</option>
                        {Object.entries(specialists).map(([id, spec]) => (
                            <option value={id} key={`specialist_${day}_interval_${recordIndex}_${id}`}>
                                {spec.name} ({spec.departments.join(', ')})
                            </option>
                        ))}
                    </FormSelect>
                </InputGroup>
            </div>
        </CustomModal>
    );
};

export default EditClientInfoModal;