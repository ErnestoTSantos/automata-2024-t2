from typing import Tuple, Set, Dict, List, Union


def load_automata(filename: str) -> Tuple[Set[str], Set[str], Dict[Tuple[str, str], Union[str, List[str]]], str, Set[str]]:
    try:
        with open(filename, 'r') as file:
            lines = file.read().splitlines()

        if len(lines) < 5:
            raise Exception("Incomplete automaton description.")

        Sigma = set(lines[0].split())  # Alphabet symbols
        Q = set(lines[1].split())  # States
        F = set(lines[2].split())  # Final states
        q0 = lines[3]  # Initial state

        if q0 not in Q:
            raise Exception("Initial state not in set of states.")

        if not F.issubset(Q):
            raise Exception("Final states not in set of states.")

        delta = {}  # Transition function

        for rule in lines[4:]:
            parts = rule.split()
            if len(parts) != 3:
                raise Exception("Invalid transition rule format.")
            origin, symbol, destination = parts
            if origin not in Q or (symbol not in Sigma and symbol != '&') or destination not in Q:
                raise Exception("Invalid rule components.")
            if (origin, symbol) not in delta:
                delta[(origin, symbol)] = destination
            else:
                if isinstance(delta[(origin, symbol)], list):
                    delta[(origin, symbol)].append(destination)
                else:
                    delta[(origin, symbol)] = [delta[(origin, symbol)], destination]

        return Q, Sigma, delta, q0, F
    except FileNotFoundError:
        raise Exception("File not found.")
    except Exception as e:
        raise Exception(f"Error loading automaton: {e}")


def process(automata: Tuple[Set[str], Set[str], Dict[Tuple[str, str], Union[str, List[str]]], str, Set[str]], words: List[str]) -> Dict[str, str]:
    Q, Sigma, delta, q0, F = automata
    dfa = convert_to_dfa(automata)
    _, _, dfa_delta, dfa_q0, dfa_F = dfa
    results = {}

    for word in words:
        current_state = dfa_q0
        valid = True
        for symbol in word:
            if symbol not in Sigma and symbol != '&':
                results[word] = "INVALIDA"
                valid = False
                break
            if (current_state, symbol) in dfa_delta:
                current_state = dfa_delta[(current_state, symbol)]
            else:
                results[word] = "REJEITA"
                valid = False
                break
        if valid:
            if current_state in dfa_F:
                results[word] = "ACEITA"
            else:
                results[word] = "REJEITA"
    return results


def epsilon_closure(state: str, delta: Dict[Tuple[str, str], Union[str, List[str]]]) -> Set[str]:
    closure = {state}
    stack = [state]
    while stack:
        current_state = stack.pop()
        if (current_state, '&') in delta:
            destinations = delta[(current_state, '&')]
            if isinstance(destinations, str):
                destinations = [destinations]
            for dest in destinations:
                if dest not in closure:
                    closure.add(dest)
                    stack.append(dest)
    return closure


def convert_to_dfa(automata: Tuple[Set[str], Set[str], Dict[Tuple[str, str], Union[str, List[str]]], str, Set[str]]) -> Tuple[Set[str], Set[str], Dict[Tuple[str, str], str], str, Set[str]]:
    Q, Sigma, delta, q0, F = automata

    new_Q = set()
    new_delta = {}
    unprocessed_states = [frozenset(epsilon_closure(q0, delta))]
    state_mapping = {frozenset(epsilon_closure(q0, delta)): 'S0'}
    new_q0 = 'S0'
    new_F = set()
    state_counter = 1

    while unprocessed_states:
        current_subset = unprocessed_states.pop()
        current_state_name = state_mapping[current_subset]

        if not current_subset.isdisjoint(F):
            new_F.add(current_state_name)

        new_Q.add(current_state_name)

        for symbol in Sigma:
            next_subset = frozenset(
                dest for state in current_subset
                if (state, symbol) in delta
                for dest in (delta[(state, symbol)] if isinstance(delta[(state, symbol)], list) else [delta[(state, symbol)]])
                for dest in epsilon_closure(dest, delta)
            )

            if next_subset:
                if next_subset not in state_mapping:
                    state_mapping[next_subset] = f'S{state_counter}'
                    unprocessed_states.append(next_subset)
                    state_counter += 1

                new_delta[(current_state_name, symbol)] = state_mapping[next_subset]

    return new_Q, Sigma, new_delta, new_q0, new_F

