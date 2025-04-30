import './App.css'
import DateRangePicker from "./components/ui/DateRangePicker/index.jsx";
import React, {useState} from "react";
import {Container} from "react-bootstrap";
import Schedule from "./components/Schedule/index.jsx";
import {WorkScheduleContextProvider} from "./contexts/WorkSchedule/provider.jsx";
import {ScheduleContextProvider} from "./contexts/Schedule/provider.jsx";

function App() {
    const [dates, setDates] = useState({fromDate: undefined, toDate: undefined});
    const onDatesChange = e => {
        const dateType = e.target.name;
        setDates({...dates, [dateType]: e.target.valueAsDate,});
    }
    return (
        <>
            <Container fluid className={'mt-2'}>
                <DateRangePicker onChange={onDatesChange} dates={dates}/>
            </Container>
            <WorkScheduleContextProvider schedule={{}}>
                <ScheduleContextProvider schedule={{}}>
                    <Schedule {...dates} />
                </ScheduleContextProvider>
            </WorkScheduleContextProvider>
        </>
    )
}

export default App
