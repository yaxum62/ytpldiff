export namespace property {
    export type Property<ValueType> = {
        value: ValueType;
        set(newValue: ValueType): void;
    };

    export function define<ValueType>(
        name: string,
        defaultValue: ValueType,
        validationFn: { (val: unknown): val is ValueType }
    ): Property<ValueType> {
        if (!validationFn(defaultValue)) {
            throw new TypeError(`default value for property '${name}' is invalid`);
        }
        if (name in registeredProperties) {
            throw new Error(`property named '${name}' is already defined`);
        }
        const ret = new PropertyImpl(name, defaultValue, validationFn);
        registeredProperties[name] = ret;
        return ret;
    }

    const registeredProperties: {
        [name: string]: PropertyImpl<unknown>;
    } = {};

    class InvalidJsonError extends Error {
        constructor(name: string, value: string) {
            super(
                `property ${name} contains value that is not a valid JSON: ${value}`
            );
            this.name = 'InvalidJsonError';
        }
    }

    class PropertyImpl<ValueType> {
        readonly name: string;
        readonly defaultValue: ValueType;
        readonly validationFn: { (val: unknown): val is ValueType };

        constructor(
            name: string,
            defaultValue: ValueType,
            validationFn: { (val: unknown): val is ValueType }
        ) {
            this.name = name;
            this.defaultValue = defaultValue;
            this.validationFn = validationFn;
        }

        get value(): ValueType {
            const value = PropertiesService.getUserProperties().getProperty(
                this.name
            );
            if (value === null) {
                return this.defaultValue;
            }
            let obj: unknown;
            try {
                obj = JSON.parse(value);
            } catch (e) {
                throw new InvalidJsonError(this.name, value);
            }
            if (this.validationFn(obj)) {
                return obj;
            }
            throw new TypeError(
                `property '${this.name}' contains value cannot be validated: '${obj}'`
            );
        }

        set(newValue: ValueType): void {
            if (!this.validationFn(newValue)) {
                throw new TypeError(
                    `assigning an invalid value to property '${this.name
                    }': ${JSON.stringify(newValue)}`
                );
            }
            PropertiesService.getUserProperties().setProperty(
                this.name,
                JSON.stringify(newValue)
            );
        }
    }
}
