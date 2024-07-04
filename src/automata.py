from typing import Tuple, Set, Dict, List, Union


def load_automata(filename: str) -> Tuple[
    Set[str], Set[str], Dict[Tuple[str, str], Union[str, List[str]]], str, Set[str]
]:
    """
    Carrega a descrição de um autômato a partir de um arquivo.

    Args:
        filename (str): O nome do arquivo contendo a descrição do autômato.

    Returns:
        Tuple[Set[str], Set[str], Dict[Tuple[str, str], Union[str, List[str]]], str, Set[str]]: 
        Uma tupla contendo os conjuntos de estados, símbolos do alfabeto, a função de transição, 
        o estado inicial e os estados finais do autômato.

    Raises:
        ValueError: Se ocorrer um erro ao carregar o autômato ou se a descrição estiver incompleta/ inválida.
    """
    try:
        with open(filename, 'r') as file:
            lines = file.read().splitlines()

        if len(lines) < 5:
            raise ValueError("Incomplete automaton description.")

        sigma = set(lines[0].split())  # Alphabet symbols
        states = set(lines[1].split())  # States
        final_states = set(lines[2].split())  # Final states
        initial_state = lines[3]  # Initial state

        if initial_state not in states:
            raise ValueError("Initial state not in set of states.")

        if not final_states.issubset(states):
            raise ValueError("Final states not in set of states.")

        delta = {}  # Transition function

        for rule in lines[4:]:
            parts = rule.split()
            if len(parts) != 3:
                raise ValueError("Invalid transition rule format.")
            origin, symbol, destination = parts
            if origin not in states or (symbol not in sigma and symbol != '&') or destination not in states:
                raise ValueError("Invalid rule components.")
            if (origin, symbol) not in delta:
                delta[(origin, symbol)] = destination
            else:
                if isinstance(delta[(origin, symbol)], list):
                    delta[(origin, symbol)].append(destination)
                else:
                    delta[(origin, symbol)] = [delta[(origin, symbol)], destination]

        return states, sigma, delta, initial_state, final_states
    except FileNotFoundError as exc:
        raise FileNotFoundError("File not found.") from exc
    except Exception as e:
        raise Exception(f"Error loading automaton: {e}") from e


def process(
    automata: Tuple[Set[str], Set[str], Dict[Tuple[str, str], Union[str, List[str]]], str, Set[str]],
    words: List[str]
) -> Dict[str, str]:
    """
    Processa uma lista de palavras utilizando o autômato fornecido.

    Args:
        automata (Tuple[Set[str], Set[str], Dict[Tuple[str, str], Union[str, List[str]]], str, Set[str]]): 
        A descrição do autômato.
        words (List[str]): A lista de palavras a serem processadas.

    Returns:
        Dict[str, str]: Um dicionário com cada palavra e seu resultado ("ACEITA", "REJEITA" ou "INVALIDA").
    """
    _, sigma, _, _, _ = automata
    dfa = convert_to_dfa(automata)
    _, _, dfa_delta, dfa_q0, dfa_f = dfa
    results = {}

    for word in words:
        current_state = dfa_q0
        valid = True
        for symbol in word:
            if symbol not in sigma and symbol != '&':
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
            if current_state in dfa_f:
                results[word] = "ACEITA"
            else:
                results[word] = "REJEITA"
    return results


def epsilon_closure(
    state: str, delta: Dict[Tuple[str, str], Union[str, List[str]]]
) -> Set[str]:
    """
    Calcula o fecho epsilon de um estado em um autômato.

    Args:
        state (str): O estado inicial.
        delta (Dict[Tuple[str, str], Union[str, List[str]]]): A função de transição do autômato.

    Returns:
        Set[str]: O conjunto de estados alcançáveis a partir do estado inicial utilizando transições epsilon.
    """
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


def convert_to_dfa(
    automata: Tuple[Set[str], Set[str], Dict[Tuple[str, str], Union[str, List[str]]], str, Set[str]]
) -> Tuple[Set[str], Set[str], Dict[Tuple[str, str], str], str, Set[str]]:
    """
    Converte um autômato não determinístico (NFA) em um autômato determinístico (DFA).

    Args:
        automata (Tuple[Set[str], Set[str], Dict[Tuple[str, str], Union[str, List[str]]], str, Set[str]]): 
        A descrição do NFA.

    Returns:
        Tuple[Set[str], Set[str], Dict[Tuple[str, str], str], str, Set[str]]: 
        A descrição do DFA resultante.
    """
    _, sigma, delta, q0, final_states = automata

    new_states = set()
    new_delta = {}
    unprocessed_states = [frozenset(epsilon_closure(q0, delta))]
    state_mapping = {frozenset(epsilon_closure(q0, delta)): 'S0'}
    new_q0 = 'S0'
    new_final_states = set()
    state_counter = 1

    while unprocessed_states:
        current_subset = unprocessed_states.pop()
        current_state_name = state_mapping[current_subset]

        if not current_subset.isdisjoint(final_states):
            new_final_states.add(current_state_name)

        new_states.add(current_state_name)

        for symbol in sigma:
            next_subset = frozenset(
                dest for state in current_subset
                if (state, symbol) in delta
                for dest in (
                    delta[(state, symbol)]
                    if isinstance(delta[(state, symbol)], list)
                    else [delta[(state, symbol)]]
                )
                for dest in epsilon_closure(dest, delta)
            )

            if next_subset:
                if next_subset not in state_mapping:
                    state_mapping[next_subset] = f'S{state_counter}'
                    unprocessed_states.append(next_subset)
                    state_counter += 1

                new_delta[(current_state_name, symbol)] = state_mapping[next_subset]

    return new_states, sigma, new_delta, new_q0, new_final_states
