import time
import optax
import haiku as hk
import jax.numpy as jnp
import jax
from torch.utils import data
import numpy as np
from data_utils import SATTrainingDataset, JraphDataLoader
from model import network_definition

NUM_EPOCHS = 10
f=0.1

# # Make a batched version of the forwarding
# batched_predict = jax.vmap(network.apply, in_axes=(None, 0))


# def loss(params, problems, targets):
#     preds = batched_predict(params, problems)
#     return -jnp.mean(preds * targets)


def one_hot(x, k, dtype=jnp.float32):
    """Create a one-hot encoding of x of size k."""
    return jnp.array(x[:, None] == jnp.arange(k), dtype)

vmap_one_hot=jax.vmap(one_hot, in_axes=(0,None), out_axes=0)

def train(path='/Users/p403830/Library/CloudStorage/OneDrive-PorscheDigitalGmbH/programming/ml_based_sat_solver/BroadcastTestSet_subset/' , rel_path='processed'): # used previously as path: "../Data/blocksworld" ## 
    sat_data = SATTrainingDataset(path)
    train_data, test_data = data.random_split(sat_data, [0.8, 0.2])

    train_loader = JraphDataLoader(train_data, batch_size=1, shuffle=True)

    network = hk.without_apply_rng(hk.transform(network_definition))
    params = network.init(jax.random.PRNGKey(42), sat_data[0][0].graph)

    opt_init, opt_update = optax.adam(1e-3)
    opt_state = opt_init(params)


    @jax.jit
    def compute_log_probs(decoded_nodes, mask, candidate):
            a=jax.nn.log_softmax(decoded_nodes) * mask[:, None]
            b= jnp.dot(candidate,a.T)
            return b

    vmap_compute_log_probs=jax.vmap(compute_log_probs, in_axes=(None,None, 0), out_axes=0)



    @jax.jit
    def update(params, opt_state, x, y, f):
            batch_masks=x[0]
            batch_graphs=x[1]
            batch_c=y[0]
            batch_e=y[1]
            #print(len(batch_masks))
            #print(len(batch_graphs))
            #print(len(batch_c))
            print(len(batch_e))
            #print(batch_e[0])
            #print(batch_e)
            loss=new_prediction_loss(params, batch_masks[0], batch_graphs[0], batch_c[0], batch_e[0], f)
            print(loss)
            g=jax.grad(new_prediction_loss)(params, batch_masks[0], batch_graphs[0], batch_c[0], batch_e[0], f)
            #g=jax.grad(batched_loss)(params, *x, c, e, f)
            ####
            updates, opt_state = opt_update(g, opt_state)
            return optax.apply_updates(params, updates), opt_state


    @jax.jit
    def prediction_loss(params, mask, graph, solution):
        decoded_nodes = network.apply(params, graph)
        solution = one_hot(solution, 2)
        # We interpret the decoded nodes as a pair of logits for each node.
        log_prob = jax.nn.log_softmax(decoded_nodes) * solution
        return -jnp.sum(log_prob * mask[:, None]) / jnp.sum(mask)


    @jax.jit
    def new_prediction_loss(params, mask, graph, candidates, energies, f: float):
            decoded_nodes = network.apply(params, graph)
            candidates = vmap_one_hot(candidates, 2)
            log_prob=vmap_compute_log_probs(decoded_nodes, mask, candidates)
            weights = jax.nn.softmax(- f * energies)
            weighted_log_probs = jax.vmap(jnp.dot,axis_name=(0,0), out_axes=0)(log_prob, weights)
            summed_weighted_log_probs=np.sum(weighted_log_probs, axis=0) #sum over all candidates
            loss=-jnp.sum(summed_weighted_log_probs @ mask[:, None]) / jnp.sum(mask)
            #print(np.shape(loss))
            return loss


    #batched_loss = jax.vmap(new_prediction_loss_single, in_axes=(None, None, None, 1,1, None), out_axes=0)

    print("Entering training loop")

    for epoch in range(NUM_EPOCHS):
        start_time = time.time()
        counter=0
        for (batch_p, batch_ce) in train_loader:
            counter=counter+1
            print("batch_number", counter)
            #batch_masks=batch_p[0]
            #batch_graphs=batch_p[1]
            #batch_c=batch_ce[0]
            #batch_e=batch_ce[1]
            #print(len(batch_masks))
            #print(len(batch_graphs))
            #print(len(batch_c))
            #print(len(batch_e))
            #print(batch_e)
            params, opt_state = update(params, opt_state, batch_p, batch_ce, f)
            print("params", np.shape(params))
        '''
        for (p, ce) in train_loader:
            #c=ce[0]
            #e=ce[1]
            for i in range(0,len(ce[1])):#,len(e)):
                params, opt_state = update(params, opt_state, p, ce[:][i], f)
            print(f"{batch} done")
        epoch_time = time.time() - start_time
        '''
        # train_acc = accuracy(params, train_images, train_labels)
        # test_acc = accuracy(params, test_images, test_labels)
        print("Epoch {} in {:0.2f} sec".format(epoch, epoch_time))

        #test_acc = jnp.mean(jnp.asarray([prediction_loss(params, p.mask, p.graph, s) for (p, s) in test_data]))

        #TBD!!!

        test_acc = jnp.mean(jnp.asarray([new_prediction_loss(p, p.graph, c, f) for (p, c) in test_data]))
        
        ##

        # print("Training set accuracy {}".format(train_acc))
        print("Test set accuracy {}".format(test_acc))

    # TODO: Save the model here

if __name__ == "__main__":
    train()

print("done")