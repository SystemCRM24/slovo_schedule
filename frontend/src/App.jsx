import './App.css'
import DateRangePicker from "./components/ui/DateRangePicker/index.jsx";
import React, {useState, useMemo} from "react";
import {Container} from "react-bootstrap";
import Schedule from "./components/Schedule/index.jsx";
import {WorkScheduleContextProvider} from "./contexts/WorkSchedule/provider.jsx";
import {ScheduleContextProvider} from "./contexts/Schedule/provider.jsx";

function App() {
    const [dates, setDates] = useState({fromDate: undefined, toDate: undefined});

    return (
        <>
            <Container fluid className={'mt-2'}>
                <DateRangePicker setDates={setDates}/>
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
