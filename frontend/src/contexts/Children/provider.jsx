import React from "react";
import {ChildrenContext} from "./context.js";

export function ChildrenContextProvider({children, childrenElements}) {
    return <ChildrenContext.Provider value={childrenElements}>{children}</ChildrenContext.Provider>
}

export function useChildrenContext() {
    const context = React.useContext(ChildrenContext);
    if (!context) throw new Error('Use context within provider!');
    return context;
}
